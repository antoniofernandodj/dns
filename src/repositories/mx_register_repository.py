# src/repositories/mx_register_repository.py

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MX_Register
from src.repositories._base import BaseRepository


class MX_RegisterRepository(BaseRepository[MX_Register]):
    """Repository para registros MX"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MX_Register)
