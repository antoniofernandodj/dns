from typing import Optional
from dnslib import (
    DNSRecord,
    RR,
    A,
    QTYPE,
    DNSQuestion,
    DNSLabel,
    MX,
    SOA,
    TXT,
    AAAA,
    CNAME,
    NS,
    SRV,
)


class A_Register:
    def __init__(self, _id: Optional[int], _host: str, _ip: str) -> None:

        self.id = _id
        self.host = _host
        self.ip = _ip

    def to_rr(self, ttl: int) -> RR:
        return RR(self.host, QTYPE.A, ttl=60, rdata=A(self.ip))

    @classmethod
    def from_rr(cls, rr: RR) -> "A_Register":

        return A_Register(_id=None, _host=rr.rname or "", _ip=str(rr.rdata))


class MX_Register:

    def __init__(
        self, _id: Optional[int], _host: str, _exchange: str, _preference: int
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
            rdata=MX(label=self.exchange, preference=self.preference),
        )

    @staticmethod
    def from_rr(rr: RR):
        return MX_Register(
            _id=None,
            _host=str(rr.rname),
            _exchange=str(rr.rdata.label),  # type: ignore
            _preference=str(rr.rdata.preference),  # type: ignore
        )


class AAAA_Register:
    def __init__(self, _id: Optional[int], _host: str, _ip: str) -> None:
        self.id = _id
        self.host = _host
        self.ip = _ip

    def to_rr(self, ttl: int) -> RR:
        return RR(self.host, QTYPE.AAAA, ttl=ttl, rdata=AAAA(self.ip))

    @classmethod
    def from_rr(cls, rr: RR) -> "AAAA_Register":
        return AAAA_Register(_id=None, _host=rr.rname, _ip=str(rr.rdata))  # type: ignore


class CNAME_Register:
    def __init__(self, _id: Optional[int], _host: str, _canonical_name: str) -> None:
        self.id = _id
        self.host = _host
        self.canonical_name = _canonical_name

    def to_rr(self, ttl: int) -> RR:
        return RR(self.host, QTYPE.CNAME, ttl=ttl, rdata=CNAME(self.canonical_name))

    @classmethod
    def from_rr(cls, rr: RR) -> "CNAME_Register":
        return CNAME_Register(
            _id=None, _host=rr.rname, _canonical_name=str(rr.rdata.label)  # type: ignore
        )


class TXT_Register:
    def __init__(self, _id: Optional[int], _host: str, _text: str) -> None:
        self.id = _id
        self.host = _host
        self.text = _text

    def to_rr(self, ttl: int) -> RR:
        return RR(self.host, QTYPE.TXT, ttl=ttl, rdata=TXT(self.text))

    @classmethod
    def from_rr(cls, rr: RR) -> "TXT_Register":
        text = "".join(part.decode("utf-8") for part in rr.rdata.data)  # type: ignore
        return TXT_Register(_id=None, _host=rr.rname or "", _text=text)


class NS_Register:
    def __init__(self, _id: Optional[int], _host: str, _nameserver: str) -> None:
        self.id = _id
        self.host = _host
        self.nameserver = _nameserver

    def to_rr(self, ttl: int) -> RR:
        return RR(self.host, QTYPE.NS, ttl=ttl, rdata=NS(self.nameserver))

    @classmethod
    def from_rr(cls, rr: RR) -> "NS_Register":
        return NS_Register(_id=None, _host=rr.rname, _nameserver=str(rr.rdata.label))  # type: ignore


class SOA_Register:
    def __init__(
        self,
        _id: Optional[int],
        _host: str,
        _mname: str,  # Master Name Server
        _rname: str,  # Responsible Person
        _serial: int,
        _refresh: int,
        _retry: int,
        _expire: int,
        _minimum: int,
    ) -> None:
        self.id = _id
        self.host = _host
        self.mname = _mname
        self.rname = _rname
        self.serial = _serial
        self.refresh = _refresh
        self.retry = _retry
        self.expire = _expire
        self.minimum = _minimum

    def to_rr(self, ttl: int) -> RR:
        return RR(
            self.host,
            QTYPE.SOA,
            ttl=ttl,
            rdata=SOA(
                mname=self.mname,
                rname=self.rname,
                times=(
                    self.serial,
                    self.refresh,
                    self.retry,
                    self.expire,
                    self.minimum,
                ),
            ),
        )

    @classmethod
    def from_rr(cls, rr: RR) -> "SOA_Register":
        rdata = rr.rdata
        # Verificar a estrutura dos dados do SOA
        serial, refresh, retry, expire, minimum = rdata.times  # type: ignore
        return SOA_Register(
            _id=None,
            _host=rr.rname,  # type: ignore
            _mname=str(rdata.mname),  # type: ignore
            _rname=str(rdata.rname),  # type: ignore
            _serial=serial,
            _refresh=refresh,
            _retry=retry,
            _expire=expire,
            _minimum=minimum,
        )


class SRV_Register:
    def __init__(
        self,
        _id: Optional[int],
        _host: str,
        _target: str,
        _port: int,
        _weight: int,
        _priority: int,
    ) -> None:
        self.id = _id
        self.host = _host
        self.target = _target
        self.port = _port
        self.weight = _weight
        self.priority = _priority

    def to_rr(self, ttl: int) -> RR:
        return RR(
            self.host,
            QTYPE.SRV,
            ttl=ttl,
            rdata=SRV(
                target=self.target,
                port=self.port,
                weight=self.weight,
                priority=self.priority,
            ),
        )

    @classmethod
    def from_rr(cls, rr: RR) -> "SRV_Register":
        return SRV_Register(
            _id=None,
            _host=rr.rname or "",
            _target=str(rr.rdata.target),  # type: ignore
            _port=rr.rdata.port,  # type: ignore
            _weight=rr.rdata.weight,  # type: ignore
            _priority=rr.rdata.priority,  # type: ignore
        )
