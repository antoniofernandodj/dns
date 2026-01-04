#!./.venv/bin/python3

"""
Servidor DNS assíncrono com cache em memória,
persistência em banco de dados,
resolução externa com Circuit Breaker e validação DNSSEC.

Fluxo de resolução:
    Cache (LRU) → Banco de Dados → Resolução Externa

"""

import asyncio
import logging
import sys
from traceback import print_exc
from typing import Any, Dict

from dnslib import AAAA, CNAME, MX, NS, QTYPE, RR, SOA, SRV, TXT, A, DNSLabel, DNSRecord

from consts import LONG_TTL, MEDIUM_TTL, TTL, DNSResolutionStatus

# Imports do projeto original
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
from src.server import DNSServer


# Configuração de logging
def setup_logging(config: AppConfig):
    """
    Configura o sistema de logging da aplicação.

    A configuração é baseada nos parâmetros definidos no AppConfig,
    incluindo nível de log, formato e destino (stdout e/ou arquivo).

    :param config: Configuração global da aplicação
    """
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format=config.logging.format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            *(
                [logging.FileHandler(config.logging.file)]
                if config.logging.file
                else []
            ),
        ],
    )
    return logger


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

    @property
    def logger(self):
        return setup_logging(self.config)

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


async def main():
    """
    Função principal de inicialização do servidor DNS.

    Responsável por:
    - Carregar configurações
    - Inicializar banco de dados
    - Configurar Circuit Breaker e DNSSEC
    - Registrar handlers por tipo de query
    - Iniciar o servidor DNS
    """

    logging.info("Database initialized")
    config = load_config()
    db = AsyncDatabase(config.database)
    await db.init_db()

    setup_logging(config)

    circuit_breaker = CircuitBreaker(
        failure_threshold=config.circuit_breaker.failure_threshold,
        timeout_duration=config.circuit_breaker.timeout_duration,
        half_open_max_calls=config.circuit_breaker.half_open_max_calls,
        name="DNS_External",
    )

    dnssec_validator = DNSSECValidator(enabled=config.security.validate_dnssec)

    server = DatabaseBackedDNSServer(
        circuit_breaker=circuit_breaker,
        host="127.0.0.1",
        port=53,
        max_requests_per_minute=10000,
        cache_cleanup_interval=60,
        dnssec_validator=dnssec_validator,
        config=config,
        db=db,
    )

    @server.query(QTYPE.A)
    async def handle_a(
        qname: DNSLabel,
        record: DNSRecord,
        cache: LRUCache,
    ):
        await server.query_with_db(
            qname_str=str(qname),
            qtype=QTYPE.A,
            response=record,
            cache=cache,
            ttl=TTL,
        )

    @server.query(QTYPE.AAAA)
    async def handle_aaaa(
        qname: DNSLabel,
        record: DNSRecord,
        cache: LRUCache,
    ):
        await server.query_with_db(
            qname_str=str(qname),
            qtype=QTYPE.AAAA,
            response=record,
            cache=cache,
            ttl=TTL,
        )

    @server.query(QTYPE.MX)
    async def handle_mx(
        qname: DNSLabel,
        record: DNSRecord,
        cache: LRUCache,
    ):
        await server.query_with_db(
            qname_str=str(qname),
            qtype=QTYPE.MX,
            response=record,
            cache=cache,
            ttl=MEDIUM_TTL,
        )

    @server.query(QTYPE.CNAME)
    async def handle_cname(
        qname: DNSLabel,
        record: DNSRecord,
        cache: LRUCache,
    ):
        await server.query_with_db(
            qname_str=str(qname),
            qtype=QTYPE.CNAME,
            response=record,
            cache=cache,
            ttl=TTL,
        )

    @server.query(QTYPE.TXT)
    async def handle_txt(
        qname: DNSLabel,
        record: DNSRecord,
        cache: LRUCache,
    ):
        await server.query_with_db(
            qname_str=str(qname),
            qtype=QTYPE.TXT,
            response=record,
            cache=cache,
            ttl=LONG_TTL,
        )

    @server.query(QTYPE.NS)
    async def handle_ns(
        qname: DNSLabel,
        record: DNSRecord,
        cache: LRUCache,
    ):
        await server.query_with_db(
            qname_str=str(qname),
            qtype=QTYPE.NS,
            response=record,
            cache=cache,
            ttl=LONG_TTL,
        )

    @server.query(QTYPE.SOA)
    async def handle_soa(
        qname: DNSLabel,
        record: DNSRecord,
        cache: LRUCache,
    ):
        await server.query_with_db(
            qname_str=str(qname),
            qtype=QTYPE.SOA,
            response=record,
            cache=cache,
            ttl=LONG_TTL,
        )

    @server.query(QTYPE.SRV)
    async def handle_srv(
        qname: DNSLabel,
        record: DNSRecord,
        cache: LRUCache,
    ):
        await server.query_with_db(
            qname_str=str(qname),
            qtype=QTYPE.SRV,
            response=record,
            cache=cache,
            ttl=LONG_TTL,
        )

    logging.info("Starting DNS server with full features:")
    logging.info("  ✓ Async concurrency (asyncio)")
    logging.info("  ✓ TTL-based cache expiration")
    logging.info("  ✓ Rate limiting per IP")
    logging.info("  ✓ Security validation")
    logging.info("  ✓ Database persistence")
    logging.info("  ✓ Complete type hints")

    try:
        await server.start()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
