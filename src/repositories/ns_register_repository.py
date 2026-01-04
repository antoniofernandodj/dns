# src/repositories/ns_register_repository.py

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import NS_Register
from src.repositories._base import BaseRepository


class NS_RegisterRepository(BaseRepository[NS_Register]):
    """Repository para registros NS"""
    def __init__(self, session: AsyncSession):
        super().__init__(session, NS_Register)
