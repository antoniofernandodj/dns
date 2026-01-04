# src/repositories/txt_register_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from src.models import TXT_Register
from src.repositories._base import BaseRepository


class TXT_RegisterRepository(BaseRepository[TXT_Register]):
    """Repository para registros TXT"""
    def __init__(self, session: AsyncSession):
        super().__init__(session, TXT_Register)
