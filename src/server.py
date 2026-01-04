# src/server.py

"""
Servidor DNS assíncrono baseado em asyncio.

Responsabilidades principais:
- Receber e processar requisições DNS via UDP
- Aplicar rate limiting por IP
- Validar segurança das queries DNS
- Resolver consultas via handlers registrados
- Utilizar cache LRU com TTL
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from dnslib import QTYPE, RR, DNSQuestion, DNSRecord  # , DNSLabel

from src.cache_lru import LRUCache
from src.config import load_config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@dataclass
class CacheEntry:
    """
    Representa uma entrada de cache DNS.

    Armazena:
    - Registro DNS (RR)
    - TTL configurado
    - Timestamp de criação
    """

    data: RR
    ttl: int
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """
        Verifica se o registro expirou com base no TTL.

        :return: True se expirado
        """
        age = time.time() - self.created_at
        return age > self.ttl

    def remaining_ttl(self) -> int:
        """
        Calcula o TTL restante do registro.

        :return: TTL restante em segundos
        """
        age = int(time.time() - self.created_at)
        remaining = self.ttl - age
        return max(0, remaining)


@dataclass
class RateLimitEntry:
    """
    Representa o estado de rate limiting para um IP.

    Controla:
    - Quantidade de requisições
    - Janela de tempo
    - Período de bloqueio
    """

    request_count: int = 0
    first_request_time: float = field(default_factory=time.time)
    blocked_until: float = 0.0

    def is_blocked(self) -> bool:
        """
        Verifica se o IP está bloqueado no momento.

        :return: True se bloqueado
        """
        return time.time() < self.blocked_until

    def should_reset(self, window_seconds: int) -> bool:
        """
        Verifica se a janela de rate limiting expirou.

        :param window_seconds: Duração da janela
        :return: True se deve resetar contadores
        """
        return time.time() - self.first_request_time > window_seconds


class DNSSecurityValidator:
    """
    Implementa validações de segurança para queries DNS.

    Protege contra:
    - Amplification attacks
    - Queries malformadas
    - Domínios inválidos
    """

    MAX_QUERY_SIZE = 512  # Tamanho máximo de query DNS (UDP padrão)
    MAX_LABEL_LENGTH = 63  # RFC 1035
    MAX_DOMAIN_LENGTH = 253  # RFC 1035

    BLOCKED_QTYPES = {
        QTYPE.ANY,  # Bloqueia ANY queries (usado em amplification attacks)
    }

    @staticmethod
    def validate_query_size(data: bytes) -> bool:
        """
        Valida o tamanho da query DNS.

        :param data: Payload da query
        :return: True se tamanho válido
        """

        return len(data) <= DNSSecurityValidator.MAX_QUERY_SIZE

    @staticmethod
    def validate_domain_name(domain: str) -> bool:
        """
        Valida o formato do nome de domínio conforme RFC 1035.

        :param domain: Nome do domínio
        :return: True se válido
        """
        if len(domain) > DNSSecurityValidator.MAX_DOMAIN_LENGTH:
            return False

        labels = domain.rstrip(".").split(".")
        if not labels:
            return False

        for label in labels:
            if not label or len(label) > DNSSecurityValidator.MAX_LABEL_LENGTH:
                return False

            # Verifica caracteres válidos (alfanuméricos e hífen)
            if not all(c.isalnum() or c == "-" for c in label):
                return False

            # Label não pode começar ou terminar com hífen
            if label.startswith("-") or label.endswith("-"):
                return False

        return True

    @staticmethod
    def is_suspicious_qtype(qtype: int) -> bool:
        """
        Verifica se o tipo de query é considerado suspeito.

        :param qtype: Tipo DNS
        :return: True se bloqueado
        """
        return qtype in DNSSecurityValidator.BLOCKED_QTYPES

    @staticmethod
    def validate_query(data: bytes, qname: str, qtype: int) -> tuple[bool, str]:
        """
        Executa validação completa de uma query DNS.

        :return: (is_valid, mensagem_de_erro)
        """
        if not DNSSecurityValidator.validate_query_size(data):
            return False, "Query size exceeds maximum"

        if not DNSSecurityValidator.validate_domain_name(qname):
            return False, "Invalid domain name format"

        if DNSSecurityValidator.is_suspicious_qtype(qtype):
            return False, f"Query type {qtype} is blocked"

        return True, ""


class RateLimiter:
    """
    Implementa rate limiting por IP usando sliding window.

    Funcionalidades:
    - Limita número de requisições por IP
    - Bloqueia IPs abusivos temporariamente
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        block_duration: int = 300,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration = block_duration
        self.clients = LRUCache[str, RateLimitEntry]()
        self._cleanup_task: asyncio.Task | None = None

    def check_rate_limit(self, client_ip: str) -> tuple[bool, str]:
        """
        Verifica se um IP pode realizar a requisição.

        :param client_ip: Endereço IP do cliente
        :return: (permitido, mensagem)
        """
        current_time = time.time()

        # Cria entrada se não existir
        if client_ip not in self.clients:
            self.clients[client_ip] = RateLimitEntry()

        entry = self.clients[client_ip]

        # Verifica se está bloqueado
        if entry.is_blocked():
            remaining = int(entry.blocked_until - current_time)
            return False, f"Rate limit exceeded. Blocked for {remaining}s"

        # Reset se a janela passou
        if entry.should_reset(self.window_seconds):
            entry.request_count = 0
            entry.first_request_time = current_time

        # Incrementa contador
        entry.request_count += 1

        # Verifica limite
        if entry.request_count > self.max_requests:
            entry.blocked_until = current_time + self.block_duration
            logging.warning(
                f"IP {client_ip} exceeded rate limit "
                f"({entry.request_count} requests in {self.window_seconds}s). "
                f"Blocked for {self.block_duration}s"
            )
            return False, f"Rate limit exceeded. Blocked for {self.block_duration}s"

        return True, ""

    def get_stats(self) -> dict[str, Any]:
        """
        Retorna estatísticas atuais do rate limiter.
        """
        blocked = sum(1 for entry in self.clients.values() if entry.is_blocked())
        return {
            "total_clients": len(self.clients),
            "blocked_clients": blocked,
            "active_clients": len(self.clients) - blocked,
        }


class DNSServer:
    """
    Servidor DNS assíncrono baseado em UDP.

    Responsável por:
    - Receber requisições DNS
    - Aplicar segurança e rate limiting
    - Encaminhar queries para handlers registrados
    - Gerenciar cache e estatísticas
    """

    def __init__(
        self,
        host: str,
        port: int,
        max_requests_per_minute: int,
        cache_cleanup_interval: int,
    ):
        self.host = host
        self.port = port
        self.s = (self.host, self.port)
        self.handlers: dict[int, Callable] = {}

        # Componentes de segurança e cache
        self.cache = LRUCache[str, int](
            max_size=load_config().cache.max_size,
            cleanup_interval=load_config().cache.cleanup_interval,
        )

        self.rate_limiter = RateLimiter(max_requests=max_requests_per_minute)
        self.security_validator = DNSSecurityValidator()

        self.cache_cleanup_interval = cache_cleanup_interval

    def query(self, qtype: int):
        """
        Decorator para registrar handlers por tipo DNS.

        :param qtype: Tipo de registro DNS (QTYPE)
        """

        def decorator(callback):
            logging.info(f"Registering handler for qtype: {qtype}")
            self.handlers[qtype] = callback
            return callback

        return decorator

    async def handle_request(
        self, data: bytes, addr: tuple[str, int], transport: asyncio.DatagramTransport
    ) -> None:
        """
        Processa uma requisição DNS recebida via UDP.

        Aplica:
        - Rate limiting
        - Validação de segurança
        - Cache
        - Dispatch para handlers
        """
        client_ip = addr[0]

        try:
            # 1. Rate limiting
            allowed, message = self.rate_limiter.check_rate_limit(client_ip)
            if not allowed:
                logging.warning(f"Blocked request from {client_ip}: {message}")
                # Envia SERVFAIL para IPs bloqueados
                request = DNSRecord.parse(data)
                response = request.reply()
                response.header.rcode = 2  # SERVFAIL
                transport.sendto(response.pack(), addr)
                return

            # 2. Parse da requisição
            request = DNSRecord.parse(data)
            response = request.reply()

            # 3. Processa cada pergunta
            for question in request.questions:
                if not isinstance(question, DNSQuestion):
                    continue

                qname_str = str(question.qname)
                qtype = question.qtype

                # 4. Validação de segurança
                is_valid, error_msg = self.security_validator.validate_query(
                    data, qname_str, qtype
                )

                if not is_valid:
                    logging.warning(
                        f"Invalid query from {client_ip}: {qname_str} - {error_msg}"
                    )
                    response.header.rcode = 5  # REFUSED
                    transport.sendto(response.pack(), addr)
                    return

                # 5. Verifica cache primeiro
                cached_rr = await self.cache.get(qname_str, qtype)
                if cached_rr:
                    response.add_answer(cached_rr)
                    logging.info(f"Served from cache: {qname_str} ({qtype})")
                    continue

                # 6. Procura handler apropriado
                handler = self.handlers.get(qtype)
                if handler is None:
                    response.header.rcode = 4  # NOT IMPLEMENTED
                    continue

                # 7. Executa handler (pode ser assíncrono)
                if asyncio.iscoroutinefunction(handler):
                    await handler(question.qname, response, self.cache)
                else:
                    handler(question.qname, response, self.cache)

            # 8. Envia resposta
            transport.sendto(response.pack(), addr)

        except Exception as e:
            logging.error(
                f"Error handling request from {client_ip}: {e}", exc_info=True
            )
            try:
                # Tenta enviar SERVFAIL em caso de erro
                request = DNSRecord.parse(data)
                response = request.reply()
                response.header.rcode = 2  # SERVFAIL
                transport.sendto(response.pack(), addr)
            except Exception:
                pass

    async def start(self) -> None:
        """
        Inicia o servidor DNS e escuta indefinidamente.
        """
        logging.info(f"Starting DNS server on {self.s}")

        # Inicia tarefas de limpeza
        self.cache.start_cleanup()

        # Cria socket UDP
        loop = asyncio.get_running_loop()

        transport, protocol = await loop.create_datagram_endpoint(
            self.create_protocol, local_addr=self.s
        )

        logging.info(f"DNS server running on {self.s}")
        logging.info(f"Protocol: {protocol}")
        logging.info(f"Cache cleanup interval: {self.cache_cleanup_interval}s")
        logging.info(
            f"Rate limit: {self.rate_limiter.max_requests} "
            f"requests per {self.rate_limiter.window_seconds}s"
        )

        try:
            await asyncio.Event().wait()  # Aguarda indefinidamente
        except KeyboardInterrupt:
            logging.info("Shutting down DNS server...")
        finally:
            transport.close()

    def create_protocol(self):
        class DNSProtocol(asyncio.DatagramProtocol):
            """
            Protocolo UDP responsável por receber datagramas DNS
            e delegar o processamento ao DNSServer.
            """

            def __init__(self, server: "DNSServer"):
                self.server = server
                self.transport: asyncio.DatagramTransport | None = None

            def connection_made(self, transport: asyncio.BaseTransport) -> None:
                self.transport = transport  # type: ignore

            def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
                """Recebe datagram e cria task assíncrona para processar"""
                asyncio.create_task(
                    self.server.handle_request(data, addr, self.transport)  # type: ignore
                )

        return DNSProtocol(self)
