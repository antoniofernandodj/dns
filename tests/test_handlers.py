# import pytest


from src.database import engine


def test_setup_database():
    from sqlalchemy import text

    with engine.connect() as connection:
        connection.execute(text("""DELETE FROM a_register"""))
        connection.execute(text("""DELETE FROM mx_register"""))
        connection.execute(text("""DELETE FROM txt_register"""))
        connection.execute(text("""DELETE FROM ns_register"""))
        connection.execute(text("""DELETE FROM soa_register"""))
        connection.execute(text("""DELETE FROM srv_register"""))

    assert True



# def test_handle_srv_query():
#     record = DNSRecord()
#     qname = DNSLabel('_ldap._tcp.example.com')

#     handle_srv_query(qname, record)

#     assert len(record.rr) > 0
#     assert str(record.rr[0].rname) == '_ldap._tcp.example.com'
