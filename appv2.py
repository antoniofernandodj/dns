from typing import Optional, List
from src.server import DnsServer
from src.repositories import (
    A_RegisterRepository,
    MX_RegisterRepository,
    AAAA_RegisterRepository,
    CNAME_RegisterRepository,
    TXT_RegisterRepository,
    NS_RegisterRepository,
    SOA_RegisterRepository,
    SRV_RegisterRepository,
)
from src.database import engine
from src.models import (
    A_Register,
    MX_Register,
    AAAA_Register,
    CNAME_Register,
    TXT_Register,
    NS_Register,
    SOA_Register,
    SRV_Register,
)
from dnslib import RR, A, AAAA, QTYPE, DNSLabel, DNSRecord, MX, CNAME, TXT, NS, SOA, SRV
import dns.resolver
import logging

# Configuração do logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

GOOGLE_DNS = "8.8.8.8"
CLOUDFLARE_DNS = "1.0.0.1"

app = DnsServer()


def resolve_externally(
    qname_str: str, rdtype: str, external_dns: List[str] = [GOOGLE_DNS, CLOUDFLARE_DNS]
) -> Optional[dns.resolver.Answer]:
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = external_dns
        answers = resolver.resolve(qname_str, rdtype)
        logging.info(f"Externally resolved answers for {qname_str}: {answers}")
        return answers
    except Exception as e:
        logging.error(f"Error resolving {qname_str} externally: {e}")
        return None


# Handler para registros do tipo 'AAAA' (Endereço IPv6)
@app.query(QTYPE.AAAA)
def handle_aaaa_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = AAAA_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing AAAA query for: {qname_str}")
        aaaa_register = repository.get_by_hostname(qname_str)
        if aaaa_register:
            logging.info(f"Locally found AAAA record: {aaaa_register}")
            record.add_answer(aaaa_register.to_rr(ttl=60))
        else:
            answers = resolve_externally(qname_str, "AAAA")
            if answers:
                ip = answers[0].address
                rr = RR(qname, QTYPE.AAAA, ttl=60, rdata=AAAA(ip))
                record.add_answer(rr)
                repository.save(AAAA_Register.from_rr(rr))


# Handler para registros do tipo 'CNAME' (Canonical Name)
@app.query(QTYPE.CNAME)
def handle_cname_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = CNAME_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing CNAME query for: {qname_str}")
        cname_register = repository.get_by_hostname(qname_str)
        if cname_register:
            logging.info(f"Locally found CNAME record: {cname_register}")
            record.add_answer(cname_register.to_rr(ttl=60))
        else:
            answers = resolve_externally(qname_str, "CNAME")
            if answers:
                cname = str(answers[0].target)
                rr = RR(qname, QTYPE.CNAME, ttl=60, rdata=CNAME(cname))
                record.add_answer(rr)
                repository.save(CNAME_Register.from_rr(rr))


# Handler para registros do tipo 'TXT' (Texto)
@app.query(QTYPE.TXT)
def handle_txt_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = TXT_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing TXT query for: {qname_str}")
        txt_register = repository.get_by_hostname(qname_str)
        if txt_register:
            logging.info(f"Locally found TXT record: {txt_register}")
            record.add_answer(txt_register.to_rr(ttl=60))
        else:
            answers = resolve_externally(qname_str, "TXT")
            if answers:
                txt = str(answers[0].strings[0])
                rr = RR(qname, QTYPE.TXT, ttl=60, rdata=TXT(txt))
                record.add_answer(rr)
                repository.save(TXT_Register.from_rr(rr))


# Handler para registros do tipo 'NS' (Nameserver)
@app.query(QTYPE.NS)
def handle_ns_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = NS_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing NS query for: {qname_str}")
        ns_register = repository.get_by_hostname(qname_str)
        if ns_register:
            logging.info(f"Locally found NS record: {ns_register}")
            record.add_answer(ns_register.to_rr(ttl=60))
        else:
            answers = resolve_externally(qname_str, "NS")
            if answers:
                nameserver = str(answers[0].target)
                rr = RR(qname, QTYPE.NS, ttl=60, rdata=NS(nameserver))
                record.add_answer(rr)
                repository.save(NS_Register.from_rr(rr))


# Handler para registros do tipo 'SOA' (Start of Authority)
@app.query(QTYPE.SOA)
def handle_soa_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = SOA_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing SOA query for: {qname_str}")
        soa_register = repository.get_by_hostname(qname_str)
        if soa_register:
            logging.info(f"Locally found SOA record: {soa_register}")
            record.add_answer(soa_register.to_rr(ttl=60))
        else:
            answers = resolve_externally(qname_str, "SOA")
            if answers:
                soa = answers[0]
                rr = RR(
                    qname,
                    QTYPE.SOA,
                    ttl=60,
                    rdata=SOA(
                        mname=soa.mname,
                        rname=soa.rname,
                        serial=soa.serial,
                        refresh=soa.refresh,
                        retry=soa.retry,
                        expire=soa.expire,
                        minimum=soa.minimum,
                    ),
                )
                record.add_answer(rr)
                repository.save(SOA_Register.from_rr(rr))


# Handler para registros do tipo 'SRV' (Service Locator)
@app.query(QTYPE.SRV)
def handle_srv_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = SRV_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing SRV query for: {qname_str}")
        srv_register = repository.get_by_hostname(qname_str)
        if srv_register:
            logging.info(f"Locally found SRV record: {srv_register}")
            record.add_answer(srv_register.to_rr(ttl=60))
        else:
            answers = resolve_externally(qname_str, "SRV")
            if answers:
                srv = answers[0]
                rr = RR(
                    qname,
                    QTYPE.SRV,
                    ttl=60,
                    rdata=SRV(
                        target=srv.target,
                        port=srv.port,
                        weight=srv.weight,
                        priority=srv.priority,
                    ),
                )
                record.add_answer(rr)
                repository.save(SRV_Register.from_rr(rr))


"""

Explicação dos Handlers
handle_aaaa_query: Processa consultas para registros AAAA (IPv6).
Se não encontrar um registro localmente, consulta externamente e salva o resultado.

handle_cname_query: Processa consultas para registros CNAME (Canonical Name).
Consulta externamente se o registro não for encontrado localmente e salva o resultado.

handle_txt_query: Processa consultas para registros TXT (Texto).
Se não encontrar o registro localmente, consulta externamente e salva o resultado.

handle_ns_query: Processa consultas para registros NS (Nameserver).
Se o registro não estiver disponível localmente, consulta externamente e salva o resultado.

handle_soa_query: Processa consultas para registros SOA (Start of Authority).
Se não encontrar o registro localmente, consulta externamente e salva o resultado.

handle_srv_query: Processa consultas para registros SRV (Service Locator).
Consulta externamente se não encontrar o registro localmente e salva o resultado.

Cada handler usa o repositório correspondente para tentar encontrar o registro localmente e,
se não for encontrado, consulta externamente, salvando os resultados na base de dados local.

"""
