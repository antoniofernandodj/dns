# src/repositories/cname_register_repository.py

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import CNAME_Register
from src.repositories._base import BaseRepository


class CNAME_RegisterRepository(BaseRepository[CNAME_Register]):
    """Repository para registros CNAME"""
    def __init__(self, session: AsyncSession):
        super().__init__(session, CNAME_Register)
