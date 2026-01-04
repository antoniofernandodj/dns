# import pytest
from dnslib import DNSLabel, DNSRecord

from app import (
    handle_a_query,
    handle_mx_query,
    handle_ns_query,
    handle_soa_query,
    handle_txt_query,
)
from src.database import engine


def test_setup_database():
    from sqlalchemy import text
    with engine.connect() as connection:
        connection.execute(text('''DELETE FROM a_register'''))
        connection.execute(text('''DELETE FROM mx_register'''))
        connection.execute(text('''DELETE FROM txt_register'''))
        connection.execute(text('''DELETE FROM ns_register'''))
        connection.execute(text('''DELETE FROM soa_register'''))
        connection.execute(text('''DELETE FROM srv_register'''))

    assert True



def test_handle_a_query():
    record = DNSRecord()
    qname = DNSLabel("example.com")

    handle_a_query(qname, record)

    assert len(record.rr) > 0
    assert str(record.rr[0].rname) == "example.com."


def test_handle_mx_query():
    record = DNSRecord()
    qname = DNSLabel("example.com")

    handle_mx_query(qname, record)

    assert len(record.rr) > 0
    assert str(record.rr[0].rname) == "example.com."


def test_handle_txt_query():
    record = DNSRecord()
    qname = DNSLabel("example.com")

    handle_txt_query(qname, record)

    assert len(record.rr) > 0
    assert str(record.rr[0].rname) == "example.com."


def test_handle_ns_query():
    record = DNSRecord()
    qname = DNSLabel("example.com")

    handle_ns_query(qname, record)

    assert len(record.rr) > 0
    assert str(record.rr[0].rname) == "example.com."


def test_handle_soa_query():
    record = DNSRecord()
    qname = DNSLabel("example.com")

    handle_soa_query(qname, record)

    assert len(record.rr) > 0
    assert str(record.rr[0].rname) == "example.com."


# def test_handle_srv_query():
#     record = DNSRecord()
#     qname = DNSLabel('_ldap._tcp.example.com')

#     handle_srv_query(qname, record)

#     assert len(record.rr) > 0
#     assert str(record.rr[0].rname) == '_ldap._tcp.example.com'
