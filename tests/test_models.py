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


from dnslib import RR, A, MX, AAAA, CNAME, TXT, NS, SOA, SRV, QTYPE


def test_a_register_to_rr():
    a_register = A_Register(_id=1, _host="example.com.", _ip="192.168.1.1")
    rr = a_register.to_rr(ttl=60)
    assert rr.rname == "example.com."
    assert rr.rtype == QTYPE.A
    assert rr.ttl == 60
    assert rr.rdata == A("192.168.1.1")


def test_a_register_from_rr():
    rr = RR("example.com.", QTYPE.A, ttl=60, rdata=A("192.168.1.1"))
    a_register = A_Register.from_rr(rr)
    assert a_register.id is None
    assert a_register.host == "example.com."
    assert a_register.ip == "192.168.1.1"


def test_mx_register_to_rr():
    mx_register = MX_Register(
        _id=1, _host="example.com.", _exchange="mail.example.com.", _preference=10
    )
    rr = mx_register.to_rr(ttl=60)
    assert rr.rname == "example.com."
    assert rr.rtype == QTYPE.MX
    assert rr.ttl == 60
    assert rr.rdata == MX("mail.example.com.", 10)


def test_mx_register_from_rr():
    rr = RR("example.com.", QTYPE.MX, ttl=60, rdata=MX("mail.example.com.", 10))
    mx_register = MX_Register.from_rr(rr)
    assert mx_register.id is None
    assert mx_register.host == "example.com."
    assert mx_register.exchange == "mail.example.com."
    assert mx_register.preference == "10"  # Note: rdata.preference might be an int


def test_aaaa_register_to_rr():
    aaaa_register = AAAA_Register(_id=1, _host="example.com.", _ip="2001:db8::1")
    rr = aaaa_register.to_rr(ttl=60)
    assert rr.rname == "example.com."
    assert rr.rtype == QTYPE.AAAA
    assert rr.ttl == 60
    assert rr.rdata == AAAA("2001:db8::1")


def test_aaaa_register_from_rr():
    rr = RR("example.com.", QTYPE.AAAA, ttl=60, rdata=AAAA("2001:db8::1"))
    aaaa_register = AAAA_Register.from_rr(rr)
    assert aaaa_register.id is None
    assert aaaa_register.host == "example.com."
    assert aaaa_register.ip == "2001:db8::1"


def test_cname_register_to_rr():
    cname_register = CNAME_Register(
        _id=1, _host="example.com.", _canonical_name="www.example.com."
    )
    rr = cname_register.to_rr(ttl=60)
    assert rr.rname == "example.com."
    assert rr.rtype == QTYPE.CNAME
    assert rr.ttl == 60
    assert rr.rdata == CNAME("www.example.com.")


def test_cname_register_from_rr():
    rr = RR("example.com.", QTYPE.CNAME, ttl=60, rdata=CNAME("www.example.com."))
    cname_register = CNAME_Register.from_rr(rr)
    assert cname_register.id is None
    assert cname_register.host == "example.com."
    assert cname_register.canonical_name == "www.example.com."


def test_txt_register_to_rr():
    txt_register = TXT_Register(
        _id=1, _host="example.com.", _text="v=spf1 include:_spf.example.com ~all"
    )
    rr = txt_register.to_rr(ttl=60)
    assert rr.rname == "example.com."
    assert rr.rtype == QTYPE.TXT
    assert rr.ttl == 60
    assert rr.rdata == TXT("v=spf1 include:_spf.example.com ~all")


def test_txt_register_from_rr():
    rr = RR(
        "example.com.",
        QTYPE.TXT,
        ttl=60,
        rdata=TXT("v=spf1 include:_spf.example.com ~all"),
    )
    txt_register = TXT_Register.from_rr(rr)
    assert txt_register.id is None
    assert txt_register.host == "example.com."
    assert txt_register.text == "v=spf1 include:_spf.example.com ~all"


def test_ns_register_to_rr():
    ns_register = NS_Register(
        _id=1, _host="example.com.", _nameserver="ns1.example.com."
    )
    rr = ns_register.to_rr(ttl=60)
    assert rr.rname == "example.com."
    assert rr.rtype == QTYPE.NS
    assert rr.ttl == 60
    assert rr.rdata == NS("ns1.example.com.")


def test_ns_register_from_rr():
    rr = RR("example.com.", QTYPE.NS, ttl=60, rdata=NS("ns1.example.com."))
    ns_register = NS_Register.from_rr(rr)
    assert ns_register.id is None
    assert ns_register.host == "example.com."
    assert ns_register.nameserver == "ns1.example.com."


def test_soa_register_to_rr():
    soa_register = SOA_Register(
        _id=1,
        _host="example.com.",
        _mname="ns1.example.com.",
        _rname="hostmaster.example.com.",
        _serial=2023082101,
        _refresh=3600,
        _retry=1800,
        _expire=1209600,
        _minimum=3600,
    )
    rr = soa_register.to_rr(ttl=60)

    assert rr.rname == "example.com."
    assert rr.rtype == QTYPE.SOA
    assert rr.ttl == 60

    assert rr.rdata.mname == "ns1.example.com."  # type: ignore
    assert rr.rdata.rname == "hostmaster.example.com."  # type: ignore
    assert rr.rdata.times[0] == 2023082101  # serial  # type: ignore
    assert rr.rdata.times[1] == 3600  # refresh  # type: ignore
    assert rr.rdata.times[2] == 1800  # retry  # type: ignore
    assert rr.rdata.times[3] == 1209600  # expire  # type: ignore
    assert rr.rdata.times[4] == 3600  # minimum  # type: ignore


def test_soa_register_from_rr():
    rr = RR(
        "example.com.",
        QTYPE.SOA,
        ttl=60,
        rdata=SOA(
            mname="ns1.example.com.",
            rname="hostmaster.example.com.",
            times=(2023082101, 3600, 1800, 1209600, 3600),
        ),
    )
    soa_register = SOA_Register.from_rr(rr)
    assert soa_register.id is None
    assert soa_register.host == "example.com."
    assert soa_register.mname == "ns1.example.com."
    assert soa_register.rname == "hostmaster.example.com."
    assert soa_register.serial == 2023082101
    assert soa_register.refresh == 3600
    assert soa_register.retry == 1800
    assert soa_register.expire == 1209600
    assert soa_register.minimum == 3600


def test_srv_register_to_rr():
    srv_register = SRV_Register(
        _id=1,
        _host="example.com.",
        _target="srv.example.com.",
        _port=5060,
        _weight=10,
        _priority=20,
    )
    rr = srv_register.to_rr(ttl=60)
    assert rr.rname == "example.com."
    assert rr.rtype == QTYPE.SRV
    assert rr.ttl == 60
    assert rr.rdata.target == "srv.example.com."  # type: ignore
    assert rr.rdata.port == 5060  # type: ignore
    assert rr.rdata.weight == 10  # type: ignore
    assert rr.rdata.priority == 20  # type: ignore


def test_srv_register_from_rr():
    rr = RR(
        "example.com.",
        QTYPE.SRV,
        ttl=60,
        rdata=SRV(target="srv.example.com.", port=5060, weight=10, priority=20),
    )
    srv_register = SRV_Register.from_rr(rr)
    assert srv_register.id is None
    assert srv_register.host == "example.com."
    assert srv_register.target == "srv.example.com."
    assert srv_register.port == 5060
    assert srv_register.weight == 10
    assert srv_register.priority == 20
