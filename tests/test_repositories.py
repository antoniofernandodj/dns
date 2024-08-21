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

from src.database import (
    a_register_table,
    mx_register_table,
    aaaa_register_table,
    cname_register_table,
    txt_register_table,
    ns_register_table,
    soa_register_table,
    srv_register_table,
)

import pytest


@pytest.fixture
def a_register_repo(connection):
    return A_RegisterRepository(connection)


@pytest.fixture
def mx_register_repo(connection):
    return MX_RegisterRepository(connection)


@pytest.fixture
def aaaa_register_repo(connection):
    return AAAA_RegisterRepository(connection)


@pytest.fixture
def cname_register_repo(connection):
    return CNAME_RegisterRepository(connection)


@pytest.fixture
def txt_register_repo(connection):
    return TXT_RegisterRepository(connection)


@pytest.fixture
def ns_register_repo(connection):
    return NS_RegisterRepository(connection)


@pytest.fixture
def soa_register_repo(connection):
    return SOA_RegisterRepository(connection)


@pytest.fixture
def srv_register_repo(connection):
    return SRV_RegisterRepository(connection)


def test_a_register_get(a_register_repo, connection):
    connection.execute(
        a_register_table.insert().values(host="example.com", ip="127.0.0.1")
    )
    result = a_register_repo.get(1)

    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.ip == "127.0.0.1"


def test_a_register_get_by_hostname(a_register_repo, connection):
    connection.execute(
        a_register_table.insert().values(host="example.com", ip="127.0.0.1")
    )
    result = a_register_repo.get_by_hostname("example.com")
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.ip == "127.0.0.1"


def test_a_register_save_new(a_register_repo, connection):
    new_register = A_Register(_id=2, _host="new.com", _ip="192.168.1.1")
    a_register_repo.save(new_register)
    result = a_register_repo.get(2)
    assert result is not None
    assert result.host == "new.com"
    assert result.ip == "192.168.1.1"


def test_a_register_save_update(a_register_repo, connection):
    connection.execute(
        a_register_table.insert().values(host="example.com", ip="127.0.0.1")
    )
    updated_register = A_Register(_id=1, _host="updated.com", _ip="192.168.1.1")
    a_register_repo.save(updated_register)
    result = a_register_repo.get(1)
    assert result is not None
    assert result.host == "updated.com"
    assert result.ip == "192.168.1.1"


def test_mx_register_get(mx_register_repo, connection):
    connection.execute(
        mx_register_table.insert().values(
            host="example.com", exchange="mail.example.com", preference=10
        )
    )
    result = mx_register_repo.get(1)
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.exchange == "mail.example.com"
    assert result.preference == 10


def test_mx_register_get_by_hostname(mx_register_repo, connection):
    connection.execute(
        mx_register_table.insert().values(
            host="example.com", exchange="mail.example.com", preference=10
        )
    )
    result = mx_register_repo.get_by_hostname("example.com")
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.exchange == "mail.example.com"
    assert result.preference == 10


def test_mx_register_get_all_by_hostname(mx_register_repo, connection):
    connection.execute(
        mx_register_table.insert().values(
            host="example.com", exchange="mail1.example.com", preference=10
        )
    )
    connection.execute(
        mx_register_table.insert().values(
            host="example.com", exchange="mail2.example.com", preference=20
        )
    )
    results = mx_register_repo.get_all_by_hostname("example.com")
    assert len(results) == 4
    assert results[-2].exchange == "mail1.example.com"
    assert results[-1].exchange == "mail2.example.com"


def test_mx_register_save_new(mx_register_repo, connection):
    new_register = MX_Register(
        _id=2, _host="new.com", _exchange="mail.new.com", _preference=10
    )
    mx_register_repo.save(new_register)
    result = mx_register_repo.get(2)
    assert result is not None
    assert result.host == "new.com"
    assert result.exchange == "mail.new.com"
    assert result.preference == 10


def test_mx_register_save_update(mx_register_repo, connection):
    connection.execute(
        mx_register_table.insert().values(
            host="example.com", exchange="mail.example.com", preference=10
        )
    )
    updated_register = MX_Register(
        _id=1, _host="example.com", _exchange="mail.updated.com", _preference=20
    )
    mx_register_repo.save(updated_register)
    result = mx_register_repo.get(1)
    assert result is not None
    assert result.host == "example.com"
    assert result.exchange == "mail.updated.com"
    assert result.preference == 20


def test_aaaa_register_get(aaaa_register_repo, connection):
    connection.execute(
        aaaa_register_table.insert().values(
            host="example.com", ip="2001:db8::ff00:42:8329"
        )
    )
    result = aaaa_register_repo.get(1)
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.ip == "2001:db8::ff00:42:8329"


def test_aaaa_register_get_by_hostname(aaaa_register_repo, connection):
    connection.execute(
        aaaa_register_table.insert().values(
            host="example.com", ip="2001:db8::ff00:42:8329"
        )
    )
    result = aaaa_register_repo.get_by_hostname("example.com")
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.ip == "2001:db8::ff00:42:8329"


def test_aaaa_register_save_new(aaaa_register_repo, connection):
    new_register = AAAA_Register(_id=2, _host="new.com", _ip="2001:db8::ff00:42:1234")
    aaaa_register_repo.save(new_register)
    result = aaaa_register_repo.get(2)
    assert result is not None
    assert result.host == "new.com"
    assert result.ip == "2001:db8::ff00:42:1234"


def test_aaaa_register_save_update(aaaa_register_repo, connection):
    connection.execute(
        aaaa_register_table.insert().values(
            host="example.com", ip="2001:db8::ff00:42:8329"
        )
    )
    updated_register = AAAA_Register(
        _id=1, _host="example.com", _ip="2001:db8::ff00:42:5678"
    )
    aaaa_register_repo.save(updated_register)
    result = aaaa_register_repo.get(1)
    assert result is not None
    assert result.host == "example.com"
    assert result.ip == "2001:db8::ff00:42:5678"


def test_cname_register_get(cname_register_repo, connection):
    connection.execute(
        cname_register_table.insert().values(
            host="example.com", canonical_name="canonical.example.com"
        )
    )
    result = cname_register_repo.get(1)
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.canonical_name == "canonical.example.com"


def test_cname_register_get_by_hostname(cname_register_repo, connection):
    connection.execute(
        cname_register_table.insert().values(
            host="example.com", canonical_name="canonical.example.com"
        )
    )
    result = cname_register_repo.get_by_hostname("example.com")
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.canonical_name == "canonical.example.com"


def test_cname_register_save_new(cname_register_repo, connection):
    new_register = CNAME_Register(
        _id=2, _host="new.com", _canonical_name="canonical.new.com"
    )
    cname_register_repo.save(new_register)
    result = cname_register_repo.get(2)
    assert result is not None
    assert result.host == "new.com"
    assert result.canonical_name == "canonical.new.com"


def test_cname_register_save_update(cname_register_repo, connection):
    connection.execute(
        cname_register_table.insert().values(
            host="example.com", canonical_name="canonical.example.com"
        )
    )
    updated_register = CNAME_Register(
        _id=1, _host="example.com", _canonical_name="updated.example.com"
    )
    cname_register_repo.save(updated_register)
    result = cname_register_repo.get(1)
    assert result is not None
    assert result.host == "example.com"
    assert result.canonical_name == "updated.example.com"


def test_txt_register_get(txt_register_repo, connection):
    connection.execute(
        txt_register_table.insert().values(host="example.com", text="v=spf1 -all")
    )
    result = txt_register_repo.get(1)
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.text == "v=spf1 -all"


def test_txt_register_get_by_hostname(txt_register_repo, connection):
    connection.execute(
        txt_register_table.insert().values(host="example.com", text="v=spf1 -all")
    )
    result = txt_register_repo.get_by_hostname("example.com")
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.text == "v=spf1 -all"


def test_txt_register_save_new(txt_register_repo, connection):
    new_register = TXT_Register(
        _id=2, _host="new.com", _text="v=spf1 include:_spf.new.com -all"
    )
    txt_register_repo.save(new_register)
    result = txt_register_repo.get(2)
    assert result is not None
    assert result.host == "new.com"
    assert result.text == "v=spf1 include:_spf.new.com -all"


def test_txt_register_save_update(txt_register_repo, connection):
    connection.execute(
        txt_register_table.insert().values(host="example.com", text="v=spf1 -all")
    )
    updated_register = TXT_Register(
        _id=1, _host="example.com", _text="v=spf1 include:_spf.example.com -all"
    )
    txt_register_repo.save(updated_register)
    result = txt_register_repo.get(1)
    assert result is not None
    assert result.host == "example.com"
    assert result.text == "v=spf1 include:_spf.example.com -all"


def test_ns_register_get(ns_register_repo, connection):
    connection.execute(
        ns_register_table.insert().values(
            host="example.com", nameserver="ns1.example.com"
        )
    )
    result = ns_register_repo.get(1)
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.nameserver == "ns1.example.com"


def test_ns_register_get_by_hostname(ns_register_repo, connection):
    connection.execute(
        ns_register_table.insert().values(
            host="example.com", nameserver="ns1.example.com"
        )
    )
    result = ns_register_repo.get_by_hostname("example.com")
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.nameserver == "ns1.example.com"


def test_ns_register_save_new(ns_register_repo, connection):
    new_register = NS_Register(_id=2, _host="new.com", _nameserver="ns2.new.com")
    ns_register_repo.save(new_register)
    result = ns_register_repo.get(2)
    assert result is not None
    assert result.host == "new.com"
    assert result.nameserver == "ns2.new.com"


def test_ns_register_save_update(ns_register_repo, connection):
    connection.execute(
        ns_register_table.insert().values(
            host="example.com", nameserver="ns1.example.com"
        )
    )
    updated_register = NS_Register(
        _id=1, _host="example.com", _nameserver="ns2.example.com"
    )
    ns_register_repo.save(updated_register)
    result = ns_register_repo.get(1)
    assert result is not None
    assert result.host == "example.com"
    assert result.nameserver == "ns2.example.com"


# Testes para SOA_RegisterRepository
def test_soa_register_get(soa_register_repo, connection):
    connection.execute(
        soa_register_table.insert().values(
            host="example.com",
            mname="ns1.example.com",
            rname="admin",
            serial=2024082101,
            refresh=3600,
            retry=600,
            expire=1209600,
            minimum=3600,
        )
    )
    result = soa_register_repo.get(1)
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.mname == "ns1.example.com"
    assert result.rname == "admin"
    assert result.serial == 2024082101
    assert result.refresh == 3600
    assert result.retry == 600
    assert result.expire == 1209600
    assert result.minimum == 3600


def test_soa_register_get_by_hostname(soa_register_repo, connection):
    connection.execute(
        soa_register_table.insert().values(
            host="example.com",
            mname="ns1.example.com",
            rname="admin",
            serial=2024082101,
            refresh=3600,
            retry=600,
            expire=1209600,
            minimum=3600,
        )
    )
    result = soa_register_repo.get_by_hostname("example.com")
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.mname == "ns1.example.com"
    assert result.rname == "admin"
    assert result.serial == 2024082101
    assert result.refresh == 3600
    assert result.retry == 600
    assert result.expire == 1209600
    assert result.minimum == 3600


def test_soa_register_save_new(soa_register_repo, connection):
    new_register = SOA_Register(
        _id=2,
        _host="new.com",
        _mname="ns2.new.com",
        _rname="admin.new.com",
        _serial=2024082102,
        _refresh=7200,
        _retry=1200,
        _expire=2419200,
        _minimum=7200,
    )
    soa_register_repo.save(new_register)
    result = soa_register_repo.get(2)
    assert result is not None
    assert result.host == "new.com"
    assert result.mname == "ns2.new.com"
    assert result.rname == "admin.new.com"
    assert result.serial == 2024082102
    assert result.refresh == 7200
    assert result.retry == 1200
    assert result.expire == 2419200
    assert result.minimum == 7200


def test_soa_register_save_update(soa_register_repo, connection):
    connection.execute(
        soa_register_table.insert().values(
            host="example.com",
            mname="ns1.example.com",
            rname="admin.example.com",
            serial=2024082101,
            refresh=3600,
            retry=600,
            expire=1209600,
            minimum=3600,
        )
    )
    updated_register = SOA_Register(
        _id=1,
        _host="example.com",
        _mname="",
        _rname="",
        _serial=2024082102,
        _refresh=7200,
        _retry=1200,
        _expire=2419200,
        _minimum=7200,
    )
    soa_register_repo.save(updated_register)
    result = soa_register_repo.get(1)
    assert result is not None
    assert result.host == "example.com"
    assert result.mname == ""
    assert result.rname == ""
    assert result.serial == 2024082102
    assert result.refresh == 7200
    assert result.retry == 1200
    assert result.expire == 2419200
    assert result.minimum == 7200


def test_srv_register_get(srv_register_repo, connection):
    connection.execute(
        srv_register_table.insert().values(
            host="example.com",
            target="sipserver.example.com",
            port=5060,
            weight=5,
            priority=10,
        )
    )
    result = srv_register_repo.get(1)
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.target == "sipserver.example.com"
    assert result.port == 5060
    assert result.weight == 5
    assert result.priority == 10


def test_srv_register_get_by_hostname(srv_register_repo, connection):
    connection.execute(
        srv_register_table.insert().values(
            host="example.com",
            target="sipserver.example.com",
            port=5060,
            weight=5,
            priority=10,
        )
    )
    result = srv_register_repo.get_by_hostname("example.com")
    assert result is not None
    assert result.id == 1
    assert result.host == "example.com"
    assert result.target == "sipserver.example.com"
    assert result.port == 5060
    assert result.weight == 5
    assert result.priority == 10


def test_srv_register_save_new(srv_register_repo, connection):
    new_register = SRV_Register(
        _id=2,
        _host="new.com",
        _target="sipserver.new.com",
        _port=5061,
        _weight=10,
        _priority=20,
    )
    srv_register_repo.save(new_register)
    result = srv_register_repo.get(2)
    assert result is not None
    assert result.host == "new.com"
    assert result.target == "sipserver.new.com"
    assert result.port == 5061
    assert result.weight == 10
    assert result.priority == 20


def test_srv_register_save_update(srv_register_repo, connection):
    connection.execute(
        srv_register_table.insert().values(
            host="example.com",
            target="sipserver.example.com",
            port=5060,
            weight=5,
            priority=10,
        )
    )
    updated_register = SRV_Register(
        _id=1,
        _host="example.com",
        _target="updatedserver.example.com",
        _port=5061,
        _weight=10,
        _priority=20,
    )
    srv_register_repo.save(updated_register)
    result = srv_register_repo.get(1)
    assert result is not None
    assert result.host == "example.com"
    assert result.target == "updatedserver.example.com"
    assert result.port == 5061
    assert result.weight == 10
    assert result.priority == 20


def test_clean_db(connection):
    from src.database import metadata

    for table in reversed(metadata.sorted_tables):
        connection.execute(table.delete())

    connection.commit()
