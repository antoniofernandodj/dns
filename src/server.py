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
import sys
from traceback import print_exc
from typing import Any, Callable, Dict, Optional

from dnslib import (  # , DNSLabel
    AAAA,
    CNAME,
    MX,
    NS,
    QTYPE,
    RR,
    SOA,
    SRV,
    TXT,
    A,
    DNSQuestion,
    DNSRecord,
)

from consts import DNSResolutionStatus

# Imports do projeto original
from security_validator import DNSSecurityValidator
from src.async_dns_resolver import AsyncDNSResolver, QTypeLiteral
from src.cache_lru import LRUCache
from src.circuit_breaker import CircuitBreaker
from src.config import AppConfig, load_config
from src.database import AsyncDatabase
from src.dns_sec_validator import DNSSECValidator
from src.models import (
    A_Register,
    AAAA_Register,
    CNAME_Register,
    MX_Register,
    NS_Register,
    SOA_Register,
    SRV_Register,
    TXT_Register,
)
from src.rate_limiter import RateLimiter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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


class DatabaseBackedDNSServer(DNSServer):
    """
    Servidor DNS que estende o DNSServer base adicionando:

    - Cache LRU em memória
    - Persistência em banco de dados assíncrono
    - Resolução externa protegida por Circuit Breaker
    - Validação DNSSEC opcional

    Hierarquia de resolução:
        Cache → Banco de Dados → DNS Externo
    """

    def __init__(
        self,
        host: str,
        port: int,
        max_requests_per_minute: int,
        cache_cleanup_interval: int,
        circuit_breaker: CircuitBreaker,
        dnssec_validator: DNSSECValidator,
        config: AppConfig,
        db: AsyncDatabase,
    ):
        """
        Inicializa o servidor DNS com dependências adicionais.

        :param host: Endereço IP de bind do servidor
        :param port: Porta UDP/TCP do DNS
        :param max_requests_per_minute: Limite de requisições por IP
        :param cache_cleanup_interval: Intervalo de limpeza do cache
        :param circuit_breaker: Circuit breaker para queries externas
        :param dnssec_validator: Validador DNSSEC
        :param config: Configuração global da aplicação
        :param db: Instância do banco de dados assíncrono
        """
        super().__init__(
            host=host,
            port=port,
            max_requests_per_minute=max_requests_per_minute,
            cache_cleanup_interval=cache_cleanup_interval,
        )

        self.config = config
        self.circuit_breaker = circuit_breaker
        self.dnssec_validator = dnssec_validator
        self.db = db
        self._logger: Optional[logging.Logger] = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = self.setup_logging()
        return self._logger

    # Configuração de logging
    def setup_logging(self):
        """
        Configura o sistema de logging da aplicação.

        A configuração é baseada nos parâmetros definidos no AppConfig,
        incluindo nível de log, formato e destino (stdout e/ou arquivo).

        :param config: Configuração global da aplicação
        """
        logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=getattr(logging, self.config.logging.level),
            format=self.config.logging.format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                *(
                    [logging.FileHandler(self.config.logging.file)]
                    if self.config.logging.file
                    else []
                ),
            ],
        )
        return logger

    async def query_with_db(
        self, qname_str: str, qtype: int, response: DNSRecord, cache: LRUCache, ttl: int
    ) -> bool:
        """
        Executa uma query DNS utilizando fallback hierárquico.

        Ordem:
            1. Cache em memória
            2. Banco de dados
            3. Resolução DNS externa

        :param qname_str: Nome do host consultado
        :param qtype: Tipo do registro DNS (QTYPE)
        :param response: Objeto DNSRecord de resposta
        :param cache: Cache LRU compartilhado
        :param ttl: TTL aplicado ao registro
        :return: True se a resolução teve sucesso
        """

        # 1. Cache
        cached_rr = await cache.get(qname_str, qtype)
        if cached_rr:
            response.add_answer(cached_rr)
            return True

        # 2. Banco de dados
        db_result = await self._query_database(qname_str, qtype, ttl)
        if db_result:
            for rr in db_result:
                response.add_answer(rr)
                await cache.set(qname_str, qtype, rr, ttl)

            logging.info(f"DB HIT: {qname_str} ({qtype})")
            return True

        # 3. Resolução externa
        return await self._query_external(qname_str, qtype, response, ttl)

    async def _query_database(
        self, qname_str: str, qtype: int, ttl: int
    ) -> list[RR] | None:
        """
        Consulta o banco de dados em busca de registros DNS.

        A consulta é executada de forma assíncrona utilizando
        repositórios específicos por tipo de registro.

        :param qname_str: Hostname consultado
        :param qtype: Tipo do registro DNS
        :param ttl: TTL aplicado ao RR
        :return: Lista de RR ou None
        """
        try:
            async with self.db.repository_factory() as factory:
                if qtype == QTYPE.A:
                    register = await factory.a_repository.get_by_hostname(qname_str)
                    return [register.to_rr(ttl)] if register else None

                elif qtype == QTYPE.AAAA:
                    register = await factory.aaaa_repository.get_by_hostname(qname_str)
                    return [register.to_rr(ttl)] if register else None

                elif qtype == QTYPE.MX:
                    registers = await factory.mx_repository.get_all_by_hostname(
                        qname_str
                    )
                    return [r.to_rr(ttl) for r in registers] if registers else None

                elif qtype == QTYPE.CNAME:
                    register = await factory.cname_repository.get_by_hostname(qname_str)
                    return [register.to_rr(ttl)] if register else None

                elif qtype == QTYPE.TXT:
                    registers = await factory.txt_repository.get_all_by_hostname(
                        qname_str
                    )
                    return [r.to_rr(ttl) for r in registers] if registers else None

                elif qtype == QTYPE.NS:
                    registers = await factory.ns_repository.get_all_by_hostname(
                        qname_str
                    )
                    return [r.to_rr(ttl) for r in registers] if registers else None

                elif qtype == QTYPE.SOA:
                    register = await factory.soa_repository.get_by_hostname(qname_str)
                    return [register.to_rr(ttl)] if register else None

                elif qtype == QTYPE.SRV:
                    registers = await factory.srv_repository.get_all_by_hostname(
                        qname_str
                    )
                    return [r.to_rr(ttl) for r in registers] if registers else None

                return None
        except Exception as e:
            print_exc()
            logging.error(f"Database query error for {qname_str}: {e}")
            return None

    def _handle_dns_error(self, response: DNSRecord, status: DNSResolutionStatus):
        """
        Ajusta o código de erro DNS (RCODE) baseado
        no status da resolução externa.

        :param response: Objeto DNSRecord de resposta
        :param status: Status da resolução DNS
        """
        if status == DNSResolutionStatus.NXDOMAIN:
            response.header.rcode = 3
        elif status in [
            DNSResolutionStatus.TIMEOUT,
            DNSResolutionStatus.NO_NAMESERVERS,
        ]:
            response.header.rcode = 2
        else:
            response.header.rcode = 2

    async def _query_external(
        self, qname_str: str, qtype: int, response: DNSRecord, ttl: int
    ) -> bool:
        """
        Executa resolução DNS externa utilizando Circuit Breaker.

        Também realiza validação DNSSEC, se habilitada, e persiste
        os resultados no banco e cache.

        :param qname_str: Hostname consultado
        :param qtype: Tipo do registro DNS
        :param response: Objeto DNSRecord de resposta
        :param ttl: TTL aplicado ao registro
        :return: True se a resolução foi bem-sucedida
        """
        qtype_map: Dict[Any, QTypeLiteral] = {
            QTYPE.A: "A",
            QTYPE.AAAA: "AAAA",
            QTYPE.MX: "MX",
            QTYPE.CNAME: "CNAME",
            QTYPE.TXT: "TXT",
            QTYPE.NS: "NS",
            QTYPE.SOA: "SOA",
            QTYPE.SRV: "SRV",
        }

        qtype_str = qtype_map.get(qtype)
        if not qtype_str:
            return False

        # Executa query através do circuit breaker
        async def external_query():
            resolver = AsyncDNSResolver(
                nameservers=self.config.dns.upstream_servers, timeout=5.0, tries=2
            )

            return await resolver.resolve(qname=qname_str, qtype=qtype_str)

        try:
            answers, status = await self.circuit_breaker.call(external_query)

            if status != DNSResolutionStatus.SUCCESS or not answers:
                self._handle_dns_error(response, status)
                return False

            # DNSSEC validation se habilitado
            if self.config.security.validate_dnssec:
                is_valid, error = await self.dnssec_validator.validate_response(
                    qname_str, qtype_str
                )

                if not is_valid:
                    self.logger.warning(
                        f"DNSSEC validation failed for {qname_str}: {error}"
                    )
                    response.header.rcode = 2  # SERVFAIL
                    return False

            await self._save_to_database(qname_str, qtype, answers, response, ttl)
            return True

        except Exception as e:
            print_exc()
            logging.error(f"External query error for {qname_str}: {e}")
            response.header.rcode = 2  # SERVFAIL
            return False

    async def _save_to_database(
        self, qname_str: str, qtype: int, answers, response: DNSRecord, ttl: int
    ) -> None:
        """
        Persiste os registros DNS no banco de dados,
        adiciona à resposta e armazena no cache.

        :param qname_str: Hostname resolvido
        :param qtype: Tipo do registro DNS
        :param answers: Respostas retornadas pelo resolver externo
        :param response: Objeto DNSRecord de resposta
        :param ttl: TTL aplicado aos registros
        """

        try:
            async with self.db.repository_factory() as factory:
                for answer in answers:
                    rr = None

                    if qtype == QTYPE.A:
                        ip = str(answer.address)
                        rr = RR(qname_str, QTYPE.A, ttl=ttl, rdata=A(ip))
                        e1 = A_Register.from_rr(rr)
                        await factory.a_repository.save(e1)

                    elif qtype == QTYPE.AAAA:
                        ip = str(answer.address)
                        rr = RR(qname_str, QTYPE.AAAA, ttl=ttl, rdata=AAAA(ip))
                        e2 = AAAA_Register.from_rr(rr)
                        await factory.aaaa_repository.save(e2)

                    elif qtype == QTYPE.MX:
                        exchange = str(answer.exchange)
                        pref = int(answer.preference)
                        rr = RR(qname_str, QTYPE.MX, ttl=ttl, rdata=MX(exchange, pref))
                        e3 = MX_Register.from_rr(rr)
                        await factory.mx_repository.save(e3)

                    elif qtype == QTYPE.CNAME:
                        cname = str(answer.target)
                        rr = RR(qname_str, QTYPE.CNAME, ttl=ttl, rdata=CNAME(cname))
                        e4 = CNAME_Register.from_rr(rr)
                        await factory.cname_repository.save(e4)

                    elif qtype == QTYPE.TXT:
                        txt_parts = [
                            s.decode("utf-8") if isinstance(s, bytes) else str(s)
                            for s in answer.strings
                        ]
                        txt = "".join(txt_parts)
                        rr = RR(qname_str, QTYPE.TXT, ttl=ttl, rdata=TXT(txt))
                        e5 = TXT_Register.from_rr(rr)
                        await factory.txt_repository.save(e5)

                    elif qtype == QTYPE.NS:
                        ns = str(answer.target)
                        rr = RR(qname_str, QTYPE.NS, ttl=ttl, rdata=NS(ns))
                        e6 = NS_Register.from_rr(rr)
                        await factory.ns_repository.save(e6)

                    elif qtype == QTYPE.SOA:
                        rr = RR(
                            qname_str,
                            QTYPE.SOA,
                            ttl=ttl,
                            rdata=SOA(
                                mname=str(answer.mname),
                                rname=str(answer.rname),
                                times=(
                                    answer.serial,
                                    answer.refresh,
                                    answer.retry,
                                    answer.expire,
                                    answer.minimum,
                                ),
                            ),
                        )
                        e7 = SOA_Register.from_rr(rr)
                        await factory.soa_repository.save(e7)

                    elif qtype == QTYPE.SRV:
                        rr = RR(
                            qname_str,
                            QTYPE.SRV,
                            ttl=ttl,
                            rdata=SRV(
                                target=str(answer.target),
                                port=answer.port,
                                weight=answer.weight,
                                priority=answer.priority,
                            ),
                        )
                        e8 = SRV_Register.from_rr(rr)
                        await factory.srv_repository.save(e8)

                    if rr:
                        response.add_answer(rr)
                        await self.cache.set(
                            qname=qname_str, qtype=qtype, data=rr, ttl=ttl
                        )
                        logging.info(f"Saved to DB: {qname_str} ({qtype})")

        except Exception as e:
            logging.error(f"Failed to save to database: {e}")
