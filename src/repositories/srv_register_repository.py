# src/repositories/srv_register_repository.py

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import SRV_Register
from src.repositories._base import BaseRepository


class SRV_RegisterRepository(BaseRepository[SRV_Register]):
    """Repository para registros SRV"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SRV_Register)
