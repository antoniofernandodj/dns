import pytest
from dnslib import DNSRecord, QTYPE, DNSLabel, RR, A
from src.server import app
from src.repositories import A_RegisterRepository
from src.models import A_Register
from unittest.mock import patch


@pytest.fixture
def a_register_repo(connection):
    return A_RegisterRepository(connection)


@patch("src.server.resolve_externally")
def test_handle_a_query_found(mock_resolve, a_register_repo, connection):
    connection.execute(
        a_register_table.insert().values(host="example.com", ip="127.0.0.1")
    )
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.A)

    mock_resolve.return_value = None  # Simulate no external resolution

    app.query(QTYPE.A)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.A
    assert rr.rdata == A("127.0.0.1")


@patch("src.server.resolve_externally")
def test_handle_a_query_not_found(mock_resolve, a_register_repo, connection):
    mock_resolve.return_value = [
        dns.resolver.Answer(
            "example.com", QTYPE.A, 60, [dns.rdatatype.from_text("A", "127.0.0.1")]
        )
    ]
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.A)

    app.query(QTYPE.A)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.A
    assert rr.rdata == A("127.0.0.1")


import pytest
from dnslib import DNSRecord, QTYPE, DNSLabel, RR, MX
from src.server import app
from src.repositories import MX_RegisterRepository
from src.models import MX_Register
from unittest.mock import patch


@pytest.fixture
def mx_register_repo(connection):
    return MX_RegisterRepository(connection)


@patch("src.server.resolve_externally")
def test_handle_mx_query_found(mock_resolve, mx_register_repo, connection):
    connection.execute(
        mx_register_table.insert().values(
            host="example.com", exchange="mail.example.com", preference=10
        )
    )
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.MX)

    mock_resolve.return_value = None  # Simulate no external resolution

    app.query(QTYPE.MX)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.MX
    assert rr.rdata == MX("mail.example.com", 10)


@patch("src.server.resolve_externally")
def test_handle_mx_query_not_found(mock_resolve, mx_register_repo, connection):
    mock_resolve.return_value = [
        dns.resolver.Answer(
            "example.com",
            QTYPE.MX,
            60,
            [dns.rdatatype.from_text("MX", "mail.example.com", 10)],
        )
    ]
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.MX)

    app.query(QTYPE.MX)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.MX
    assert rr.rdata == MX("mail.example.com", 10)


import pytest
from dnslib import DNSRecord, QTYPE, DNSLabel, RR, AAAA
from src.server import app
from src.repositories import AAAA_RegisterRepository
from src.models import AAAA_Register
from unittest.mock import patch


@pytest.fixture
def aaaa_register_repo(connection):
    return AAAA_RegisterRepository(connection)


@patch("src.server.resolve_externally")
def test_handle_aaaa_query_found(mock_resolve, aaaa_register_repo, connection):
    connection.execute(
        aaaa_register_table.insert().values(
            host="example.com", ip="2001:db8::ff00:42:8329"
        )
    )
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.AAAA)

    mock_resolve.return_value = None  # Simulate no external resolution

    app.query(QTYPE.AAAA)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.AAAA
    assert rr.rdata == AAAA("2001:db8::ff00:42:8329")


@patch("src.server.resolve_externally")
def test_handle_aaaa_query_not_found(mock_resolve, aaaa_register_repo, connection):
    mock_resolve.return_value = [
        dns.resolver.Answer(
            "example.com",
            QTYPE.AAAA,
            60,
            [dns.rdatatype.from_text("AAAA", "2001:db8::ff00:42:8329")],
        )
    ]
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.AAAA)

    app.query(QTYPE.AAAA)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.AAAA
    assert rr.rdata == AAAA("2001:db8::ff00:42:8329")


import pytest
from dnslib import DNSRecord, QTYPE, DNSLabel, RR, CNAME
from src.server import app
from src.repositories import CNAME_RegisterRepository
from src.models import CNAME_Register
from unittest.mock import patch


@pytest.fixture
def cname_register_repo(connection):
    return CNAME_RegisterRepository(connection)


@patch("src.server.resolve_externally")
def test_handle_cname_query_found(mock_resolve, cname_register_repo, connection):
    connection.execute(
        cname_register_table.insert().values(
            host="example.com", canonical_name="canonical.example.com"
        )
    )
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.CNAME)

    mock_resolve.return_value = None  # Simulate no external resolution

    app.query(QTYPE.CNAME)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.CNAME
    assert rr.rdata == CNAME("canonical.example.com")


@patch("src.server.resolve_externally")
def test_handle_cname_query_not_found(mock_resolve, cname_register_repo, connection):
    mock_resolve.return_value = [
        dns.resolver.Answer(
            "example.com",
            QTYPE.CNAME,
            60,
            [dns.rdatatype.from_text("CNAME", "canonical.example.com")],
        )
    ]
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.CNAME)

    app.query(QTYPE.CNAME)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.CNAME
    assert rr.rdata == CNAME("canonical.example.com")


import pytest
from dnslib import DNSRecord, QTYPE, DNSLabel, RR, TXT
from src.server import app
from src.repositories import TXT_RegisterRepository
from src.models import TXT_Register
from unittest.mock import patch


@pytest.fixture
def txt_register_repo(connection):
    return TXT_RegisterRepository(connection)


@patch("src.server.resolve_externally")
def test_handle_txt_query_found(mock_resolve, txt_register_repo, connection):
    connection.execute(
        txt_register_table.insert().values(host="example.com", text="v=spf1 -all")
    )
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.TXT)

    mock_resolve.return_value = None  # Simulate no external resolution

    app.query(QTYPE.TXT)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.TXT
    assert rr.rdata == TXT("v=spf1 -all")


@patch("src.server.resolve_externally")
def test_handle_txt_query_not_found(mock_resolve, txt_register_repo, connection):
    mock_resolve.return_value = [
        dns.resolver.Answer(
            "example.com",
            QTYPE.TXT,
            60,
            [dns.rdatatype.from_text("TXT", "v=spf1 -all")],
        )
    ]
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.TXT)

    app.query(QTYPE.TXT)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.TXT
    assert rr.rdata == TXT("v=spf1 -all")


import pytest
from dnslib import DNSRecord, QTYPE, DNSLabel, RR, NS
from src.server import app
from src.repositories import NS_RegisterRepository
from src.models import NS_Register
from unittest.mock import patch


@pytest.fixture
def ns_register_repo(connection):
    return NS_RegisterRepository(connection)


@patch("src.server.resolve_externally")
def test_handle_ns_query_found(mock_resolve, ns_register_repo, connection):
    connection.execute(
        ns_register_table.insert().values(
            host="example.com", nameserver="ns.example.com"
        )
    )
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.NS)

    mock_resolve.return_value = None  # Simulate no external resolution

    app.query(QTYPE.NS)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.NS
    assert rr.rdata == NS("ns.example.com")


@patch("src.server.resolve_externally")
def test_handle_ns_query_not_found(mock_resolve, ns_register_repo, connection):
    mock_resolve.return_value = [
        dns.resolver.Answer(
            "example.com",
            QTYPE.NS,
            60,
            [dns.rdatatype.from_text("NS", "ns.example.com")],
        )
    ]
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.NS)

    app.query(QTYPE.NS)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.NS
    assert rr.rdata == NS("ns.example.com")


import pytest
from dnslib import DNSRecord, QTYPE, DNSLabel, RR, SOA
from src.server import app
from src.repositories import SOA_RegisterRepository
from src.models import SOA_Register
from unittest.mock import patch


@pytest.fixture
def soa_register_repo(connection):
    return SOA_RegisterRepository(connection)


@patch("src.server.resolve_externally")
def test_handle_soa_query_found(mock_resolve, soa_register_repo, connection):
    connection.execute(
        soa_register_table.insert().values(
            host="example.com",
            mname="ns.example.com",
            rname="admin.example.com",
            serial=2023082101,
            refresh=3600,
            retry=1800,
            expire=1209600,
            minimum=3600,
        )
    )
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.SOA)

    mock_resolve.return_value = None  # Simulate no external resolution

    app.query(QTYPE.SOA)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.SOA
    assert rr.rdata == SOA(
        mname="ns.example.com",
        rname="admin.example.com",
        serial=2023082101,
        refresh=3600,
        retry=1800,
        expire=1209600,
        minimum=3600,
    )


@patch("src.server.resolve_externally")
def test_handle_soa_query_not_found(mock_resolve, soa_register_repo, connection):
    mock_resolve.return_value = [
        dns.resolver.Answer(
            "example.com",
            QTYPE.SOA,
            60,
            [
                dns.rdatatype.from_text(
                    "SOA",
                    "ns.example.com",
                    "admin.example.com",
                    2023082101,
                    3600,
                    1800,
                    1209600,
                    3600,
                )
            ],
        )
    ]
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.SOA)

    app.query(QTYPE.SOA)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.SOA
    assert rr.rdata == SOA(
        mname="ns.example.com",
        rname="admin.example.com",
        serial=2023082101,
        refresh=3600,
        retry=1800,
        expire=1209600,
        minimum=3600,
    )


import pytest
from dnslib import DNSRecord, QTYPE, DNSLabel, RR, SRV
from src.server import app
from src.repositories import SRV_RegisterRepository
from src.models import SRV_Register
from unittest.mock import patch


@pytest.fixture
def srv_register_repo(connection):
    return SRV_RegisterRepository(connection)


@patch("src.server.resolve_externally")
def test_handle_srv_query_found(mock_resolve, srv_register_repo, connection):
    connection.execute(
        srv_register_table.insert().values(
            host="example.com", target="srv.example.com", port=80, weight=10, priority=1
        )
    )
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.SRV)

    mock_resolve.return_value = None  # Simulate no external resolution

    app.query(QTYPE.SRV)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.SRV
    assert rr.rdata == SRV("srv.example.com", 80, 10, 1)


@patch("src.server.resolve_externally")
def test_handle_srv_query_not_found(mock_resolve, srv_register_repo, connection):
    mock_resolve.return_value = [
        dns.resolver.Answer(
            "example.com",
            QTYPE.SRV,
            60,
            [dns.rdatatype.from_text("SRV", "srv.example.com", 80, 10, 1)],
        )
    ]
    qname = DNSLabel("example.com")
    record = DNSRecord.question(qname, QTYPE.SRV)

    app.query(QTYPE.SRV)(qname, record)

    assert len(record.rr) == 1
    rr = record.rr[0]
    assert rr.rtype == QTYPE.SRV
    assert rr.rdata == SRV("srv.example.com", 80, 10, 1)
