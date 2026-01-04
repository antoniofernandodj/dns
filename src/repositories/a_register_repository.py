# src/repositories/a_register_repository.py

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import A_Register
from src.repositories._base import BaseRepository


class A_RegisterRepository(BaseRepository[A_Register]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, A_Register)
