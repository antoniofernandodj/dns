from typing import Optional
from src.server import DnsServer
from src.database import (
    A_RegisterRepository,
    MX_RegisterRepository,
    engine, init_mappers
)
from src.models import A_Register, MX_Register
from dnslib import RR, A, QTYPE, DNSLabel, DNSRecord, MX
import dns.resolver

GOOGLE_DNS = '8.8.8.8'
CLOUDFLARE_DNS = "1.0.0.1"

app = DnsServer()


def resolve_externally(
    qname_str,
    rdtype,
    external_dns = [GOOGLE_DNS, GOOGLE_DNS]
) -> Optional[dns.resolver.Answer]:

    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = external_dns
        answers = resolver.resolve(qname_str, rdtype)
        print(f'Externally answer resolved!: {answers}')

        return answers
    except Exception as e:
        print(f"Error resolving {qname_str} externally: {e}")
        return None


# Handler para registros do tipo 'A' (Endereço IPv4)
@app.handle_query(QTYPE.A)
def handle_a_query(qname: DNSLabel, record: DNSRecord) -> None:
    with engine.connect() as connection:
        repository = A_RegisterRepository(connection)
        qname_str = str(qname)
        print(f"Processing query for: {qname_str}")
        a_register = repository.get_by_hostname(qname_str)
        if a_register:
            print(f'Item {a_register} locally found!')
            record.add_answer(a_register.to_rr(ttl=60))
            return None

        answers = resolve_externally(qname_str, 'A')
        if answers:
            answer = answers[0]

            ip = answer.address
            print({'answer.address': answer.address, "answer": answer})

            rr = RR(qname, QTYPE.A, ttl=60, rdata=A(ip))
            record.add_answer(rr)
            repository.save(A_Register.from_rr(rr))


# Handler para registros do tipo 'MX' (Mail Exchange)
@app.handle_query(QTYPE.MX)
def handle_mx_query(qname: DNSLabel, record: DNSRecord):
    with engine.connect() as connection:
        repository = MX_RegisterRepository(connection)
        qname_str = str(qname)
        print(f"Processing MX query for: {qname_str}")
        
        mx_registers = repository.get_all_by_hostname(qname_str)
        print({'mx_registers': mx_registers})
        if mx_registers:
            for mx_register in mx_registers:
                print(f'Item {mx_register} locally found!')
                record.add_answer(mx_register.to_rr(ttl=300))
            
            return None

        answers = resolve_externally(qname_str, 'MX')
        for answer in answers:
            host, pref = str(answer.exchange), answer.preference

            rr = RR(qname_str, QTYPE.MX, ttl=60, rdata=MX(host, pref))
            record.add_answer(rr)
            repository.save(MX_Register.from_rr(rr))


if __name__ == "__main__":
    init_mappers()
    app.run(port=53)
