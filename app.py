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
from src.circuit_breaker import CircuitBreaker
from src.config import load_config
from src.database import AsyncDatabase
from src.dns_sec_validator import DNSSECValidator
from src.server import DatabaseBackedDNSServer

config = load_config()
db = AsyncDatabase(config.database)

circuit_breaker = CircuitBreaker(
    failure_threshold=config.circuit_breaker.failure_threshold,
    timeout_duration=config.circuit_breaker.timeout_duration,
    half_open_max_calls=config.circuit_breaker.half_open_max_calls,
    name=config.name,
)

dnssec_validator = DNSSECValidator(enabled=config.security.validate_dnssec)

server = DatabaseBackedDNSServer(
    circuit_breaker=circuit_breaker,
    host=config.server.host,
    port=config.server.port,
    max_requests_per_minute=config.rate_limit.max_requests,
    cache_cleanup_interval=config.cache.cleanup_interval,
    dnssec_validator=dnssec_validator,
    config=config,
    db=db,
)


@server.query(QTYPE.A)
async def handle_a(qname: DNSLabel, record: DNSRecord):
    await server.query_with_db(qname, QTYPE.A, record, TTL)


@server.query(QTYPE.AAAA)
async def handle_aaaa(qname: DNSLabel, record: DNSRecord):
    await server.query_with_db(qname, QTYPE.AAAA, record, TTL)


@server.query(QTYPE.MX)
async def handle_mx(qname: DNSLabel, record: DNSRecord):
    await server.query_with_db(qname, QTYPE.MX, record, MEDIUM_TTL)


@server.query(QTYPE.CNAME)
async def handle_cname(qname: DNSLabel, record: DNSRecord):
    await server.query_with_db(qname, QTYPE.CNAME, record, TTL)


@server.query(QTYPE.TXT)
async def handle_txt(qname: DNSLabel, record: DNSRecord):
    await server.query_with_db(qname, QTYPE.TXT, record, LONG_TTL)


@server.query(QTYPE.NS)
async def handle_ns(qname: DNSLabel, record: DNSRecord):
    await server.query_with_db(qname, QTYPE.NS, record, LONG_TTL)


@server.query(QTYPE.SOA)
async def handle_soa(qname: DNSLabel, record: DNSRecord):
    await server.query_with_db(qname, QTYPE.SOA, record, LONG_TTL)


@server.query(QTYPE.SRV)
async def handle_srv(qname: DNSLabel, record: DNSRecord):
    await server.query_with_db(qname, QTYPE.SRV, record, LONG_TTL)



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

    server.setup_logging()

    logging.info("Database initialized")

    await db.init_db()

    logging.info("Starting DNS server with full features:")
    logging.info("  ✓ Async concurrency (asyncio)")
    logging.info("  ✓ TTL-based cache expiration")
    logging.info("  ✓ Rate limiting per IP")
    logging.info("  ✓ Security validation")
    logging.info("  ✓ Database persistence")
    logging.info("  ✓ Complete type hints")

    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
