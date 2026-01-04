# src/database.py

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import registry
from sqlalchemy.sql.schema import Column, MetaData, Table
from sqlalchemy.types import Integer, String

from src.config import DatabaseConfig, load_config
from src.models import (
    A_Register,
    AAAA_Register,
    CNAME_Register,
    MX_Register,
    NS_Register,
    SOA_Register,
    SRV_Register,
    TXT_Register,
)

config = load_config().database

metadata = MetaData()

engine = create_async_engine(
    config.url,
    echo=config.echo,
    pool_size=config.pool_size,
    max_overflow=config.max_overflow,
    pool_timeout=config.pool_timeout,
    pool_recycle=config.pool_recycle,
    pool_pre_ping=True,
)

a_register_table = Table(
    "a_register",
    metadata,
    Column[int]("id", Integer, primary_key=True),
    Column[str]("host", String(100)),
    Column[str]("ip", String(100)),
)

mx_register_table = Table(
    "mx_register",
    metadata,
    Column[int]("id", Integer, primary_key=True),
    Column[str]("host", String(100), nullable=False),
    Column[str]("exchange", String(100), nullable=False),
    Column[int]("preference", Integer, nullable=False),
)

aaaa_register_table = Table(
    "aaaa_register",
    metadata,
    Column[int]("id", Integer, primary_key=True),
    Column[str]("host", String(100)),
    Column[str]("ip", String(100)),
)

cname_register_table = Table(
    "cname_register",
    metadata,
    Column[int]("id", Integer, primary_key=True),
    Column[str]("host", String(100)),
    Column[str]("canonical_name", String(100)),
)

txt_register_table = Table(
    "txt_register",
    metadata,
    Column[int]("id", Integer, primary_key=True),
    Column[str]("host", String(100)),
    Column[str]("text", String(255)),  # Considera que o texto pode ser mais longo
)

ns_register_table = Table(
    "ns_register",
    metadata,
    Column[int]("id", Integer, primary_key=True),
    Column[str]("host", String(100)),
    Column[str]("nameserver", String(100)),
)

soa_register_table = Table(
    "soa_register",
    metadata,
    Column[int]("id", Integer, primary_key=True),
    Column[str]("host", String(100)),
    Column[str]("mname", String(100)),  # Master Name Server
    Column[str]("rname", String(100)),  # Responsible Person
    Column[int]("serial", Integer),  # Serial Number
    Column[int]("refresh", Integer),  # Refresh Interval
    Column[int]("retry", Integer),  # Retry Interval
    Column[int]("expire", Integer),  # Expiry Limit
    Column[int]("minimum", Integer),  # Minimum TTL
)

srv_register_table = Table(
    "srv_register",
    metadata,
    Column[int]("id", Integer, primary_key=True),
    Column[str]("host", String(100)),
    Column[str]("target", String(100)),  # Target Host
    Column[int]("port", Integer),  # Port Number
    Column[int]("weight", Integer),  # Weight
    Column[int]("priority", Integer),  # Priority
)






class AsyncDatabase:
    """Gerenciador de banco de dados assíncrono"""

    @property
    def logger(self):
        return logging.getLogger('AsyncDatabase.' + __name__)

    def __init__(self, config: DatabaseConfig):
        self.mapper_registry = registry()
        self.config = config
        self.engine = create_async_engine(
            config.url,
            echo=config.echo,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=True,
        )
        self.async_session_maker = async_sessionmaker[AsyncSession](
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Inicializa o banco de dados"""

        self.mapper_registry.map_imperatively(A_Register, a_register_table)
        self.mapper_registry.map_imperatively(MX_Register, mx_register_table)
        self.mapper_registry.map_imperatively(AAAA_Register, aaaa_register_table)
        self.mapper_registry.map_imperatively(CNAME_Register, cname_register_table)
        self.mapper_registry.map_imperatively(TXT_Register, txt_register_table)
        self.mapper_registry.map_imperatively(NS_Register, ns_register_table)
        self.mapper_registry.map_imperatively(SOA_Register, soa_register_table)
        self.mapper_registry.map_imperatively(SRV_Register, srv_register_table)

        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        self.logger.info("Database initialized")

    async def close(self):
        """Fecha conexões do banco"""
        await self.engine.dispose()
        self.logger.info("Database connections closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager para sessões"""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def repository_factory(self):
        """Context manager para sessões"""
        from src.repositories.repository_factory import RepositoryFactory
        async with self.async_session_maker() as session:
            try:
                factory = RepositoryFactory(session)
                yield factory
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def get_pool_status():
        sync_pool = engine.sync_engine.pool
        return {
            "size": sync_pool.size(),
            "checked_in": sync_pool.checkedin(),
            "checked_out": sync_pool.checkedout(),
            "overflow": sync_pool.overflow(),
            "total": sync_pool.size() + sync_pool.overflow(),
        }
