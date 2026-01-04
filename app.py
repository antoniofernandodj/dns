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

from dnslib import QTYPE, DNSLabel, DNSRecord

from consts import LONG_TTL, MEDIUM_TTL, TTL

# Imports do projeto original
from src.cache_lru import LRUCache
from src.circuit_breaker import CircuitBreaker
from src.config import load_config
from src.database import AsyncDatabase
from src.dns_sec_validator import DNSSECValidator
from src.server import DatabaseBackedDNSServer


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

    server.setup_logging()

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
