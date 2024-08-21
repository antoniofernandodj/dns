from typing import Optional
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

from sqlalchemy.sql import select
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.schema import Table, Column, MetaData
from sqlalchemy.types import Integer, String
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import registry

metadata = MetaData()

engine = create_engine("sqlite:///example.db", echo=False)

a_register_table = Table(
    "a_register",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("host", String(100)),
    Column("ip", String(100)),
)

mx_register_table = Table(
    "mx_register",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("host", String(100), nullable=False),
    Column("exchange", String(100), nullable=False),
    Column("preference", Integer, nullable=False),
)

aaaa_register_table = Table(
    "aaaa_register",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("host", String(100)),
    Column("ip", String(100)),
)

cname_register_table = Table(
    "cname_register",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("host", String(100)),
    Column("canonical_name", String(100)),
)

txt_register_table = Table(
    "txt_register",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("host", String(100)),
    Column("text", String(255)),  # Considera que o texto pode ser mais longo
)

ns_register_table = Table(
    "ns_register",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("host", String(100)),
    Column("nameserver", String(100)),
)

soa_register_table = Table(
    "soa_register",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("host", String(100)),
    Column("mname", String(100)),  # Master Name Server
    Column("rname", String(100)),  # Responsible Person
    Column("serial", Integer),  # Serial Number
    Column("refresh", Integer),  # Refresh Interval
    Column("retry", Integer),  # Retry Interval
    Column("expire", Integer),  # Expiry Limit
    Column("minimum", Integer),  # Minimum TTL
)

srv_register_table = Table(
    "srv_register",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("host", String(100)),
    Column("target", String(100)),  # Target Host
    Column("port", Integer),  # Port Number
    Column("weight", Integer),  # Weight
    Column("priority", Integer),  # Priority
)


def init_mappers():
    mapper_registry = registry()
    metadata.create_all(bind=engine)

    mapper_registry.map_imperatively(A_Register, a_register_table)
    mapper_registry.map_imperatively(MX_Register, mx_register_table)

    mapper_registry.map_imperatively(AAAA_Register, aaaa_register_table)
    mapper_registry.map_imperatively(CNAME_Register, cname_register_table)
    mapper_registry.map_imperatively(TXT_Register, txt_register_table)
    mapper_registry.map_imperatively(NS_Register, ns_register_table)
    mapper_registry.map_imperatively(SOA_Register, soa_register_table)
    mapper_registry.map_imperatively(SRV_Register, srv_register_table)
