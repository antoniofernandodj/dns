
from typing import Optional
from dnslib import DNSRecord, RR, A, QTYPE, DNSQuestion, DNSLabel, MX


class A_Register:
    def __init__(
        self,
        _id: Optional[int],
        _host: str,
        _ip: str
    ) -> None:

        self.id = _id
        self.host = _host
        self.ip = _ip

    def to_rr(self, ttl: int) -> RR:
        return RR(
            self.host,
            QTYPE.A,
            ttl=60,
            rdata=A(self.ip)
        )
    
    @classmethod
    def from_rr(cls, rr: RR) -> 'A_Register':

        return A_Register(
            _id=None,
            _host=rr.rname,
            _ip=str(rr.rdata)
        )


class MX_Register:

    def __init__(
        self,
        _id: Optional[int],
        _host: str,
        _exchange: str,
        _preference: str
    ) -> None:

        self.id = _id
        self.host = _host
        self.exchange = _exchange
        self.preference = _preference

    def to_rr(self, ttl: int):
        return RR(
            self.host,
            QTYPE.MX,
            ttl=ttl,
            rdata=MX(label=self.exchange, preference=self.preference)
        )

    @staticmethod
    def from_rr(rr: RR):
        return MX_Register(
            _id=None,
            _host=str(rr.rname),
            _exchange=str(rr.rdata.label),
            _preference=str(rr.rdata.preference)
        )