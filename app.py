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
from src.database import (
    engine,
    init_mappers,
)

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


# Handler para registros do tipo 'A' (Endereço IPv4)
@app.query(QTYPE.A)
def handle_a_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = A_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing A query for: {qname_str}")
        a_register = repository.get_by_hostname(qname_str)
        if a_register:
            logging.info(f"Locally found A record: {a_register}")
            record.add_answer(a_register.to_rr(ttl=60))
        else:
            answers = resolve_externally(qname_str, "A")
            if answers:
                ip = answers[0].address
                rr = RR(qname, QTYPE.A, ttl=60, rdata=A(ip))
                record.add_answer(rr)
                repository.save(A_Register.from_rr(rr))



# Handler para registros do tipo 'MX' (Mail Exchange)
@app.query(QTYPE.MX)
def handle_mx_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = MX_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing MX query for: {qname_str}")
        mx_registers = repository.get_all_by_hostname(qname_str)
        if mx_registers:
            for mx_register in mx_registers:
                logging.info(f"Locally found MX record: {mx_register}")
                record.add_answer(mx_register.to_rr(ttl=300))
        else:
            answers = resolve_externally(qname_str, "MX")
            if answers:
                for answer in answers:
                    host, pref = str(answer.exchange), answer.preference
                    rr = RR(qname_str, QTYPE.MX, ttl=60, rdata=MX(host, pref))
                    record.add_answer(rr)
                    repository.save(MX_Register.from_rr(rr))


# Handler para registros do tipo 'TXT' (Texto)
@app.query(QTYPE.TXT)
def handle_txt_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = TXT_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing TXT query for: {qname_str}")
        txt_registers = repository.get_all_by_hostname(qname_str)
        if txt_registers:
            for txt_register in txt_registers:
                logging.info(f"Locally found TXT record: {txt_register}")
                record.add_answer(txt_register.to_rr(ttl=3600))
        else:
            answers = resolve_externally(qname_str, "TXT")
            if answers:
                for answer in answers:
                    text = str(answer.strings[0])
                    rr = RR(qname_str, QTYPE.TXT, ttl=3600, rdata=TXT(text))
                    record.add_answer(rr)
                    repository.save(TXT_Register.from_rr(rr))


# Handler para registros do tipo 'NS' (Nameserver)
@app.query(QTYPE.NS)
def handle_ns_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = NS_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing NS query for: {qname_str}")
        ns_registers = repository.get_all_by_hostname(qname_str)
        if ns_registers:
            for ns_register in ns_registers:
                logging.info(f"Locally found NS record: {ns_register}")
                record.add_answer(ns_register.to_rr(ttl=3600))
        else:
            answers = resolve_externally(qname_str, "NS")
            if answers:
                for answer in answers:
                    ns = str(answer.target)
                    rr = RR(qname_str, QTYPE.NS, ttl=3600, rdata=NS(ns))
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
            record.add_answer(soa_register.to_rr(ttl=3600))
        else:
            answers = resolve_externally(qname_str, "SOA")
            if answers:
                soa = answers[0]
                rr = RR(
                    qname_str,
                    QTYPE.SOA,
                    ttl=3600,
                    rdata=SOA(
                        soa.mname,
                        soa.rname,
                        soa.serial,
                        soa.refresh,
                        soa.retry,
                        soa.expire,
                        soa.minimum,
                    ),
                )
                record.add_answer(rr)
                repository.save(SOA_Register.from_rr(rr))


# Handler para registros do tipo 'SRV' (Service)
@app.query(QTYPE.SRV)
def handle_srv_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = SRV_RegisterRepository(connection)
        qname_str = str(qname)

        logging.info(f"Processing SRV query for: {qname_str}")
        srv_registers = repository.get_all_by_hostname(qname_str)
        if srv_registers:
            for srv_register in srv_registers:
                logging.info(f"Locally found SRV record: {srv_register}")
                record.add_answer(srv_register.to_rr(ttl=3600))
        else:
            answers = resolve_externally(qname_str, "SRV")
            if answers:
                for answer in answers:
                    rr = RR(
                        qname_str,
                        QTYPE.SRV,
                        ttl=3600,
                        rdata=SRV(
                            answer.target, answer.port, answer.weight, answer.priority
                        ),
                    )
                    record.add_answer(rr)
                    repository.save(SRV_Register.from_rr(rr))


if __name__ == "__main__":
    init_mappers()
    app.run(port=53)
