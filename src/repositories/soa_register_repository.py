# src/repositories/soa_register_repository.py

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import SOA_Register
from src.repositories._base import BaseRepository


class SOA_RegisterRepository(BaseRepository[SOA_Register]):
    """Repository para registros SOA"""
    def __init__(self, session: AsyncSession):
        super().__init__(session, SOA_Register)
