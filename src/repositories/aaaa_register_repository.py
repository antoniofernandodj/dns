# src/repositories/aaaa_register_repository.py

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AAAA_Register
from . import BaseRepository


class AAAA_RegisterRepository(BaseRepository[AAAA_Register]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AAAA_Register)
