# src/repositories/_base.py

from abc import ABC
from typing import Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


Model = TypeVar('Model')
class BaseRepository(ABC, Generic[Model]):
    """Classe base para repositórios com métodos comuns"""
    
    def __init__(self, session: AsyncSession, model: Type[Model]):
        self._session = session
        self.model = model
    
    @property
    def session(self) -> AsyncSession:
        return self._session

    async def get(self, register_id: int) -> Optional[Model]:
        query = select(self.model).filter_by(id=register_id)
        result = await self.session.execute(query)
            
        return result.scalars().first()

    async def get_by_hostname(self, hostname: str) -> Optional[Model]:
        query = select(self.model).filter_by(host=hostname)
        result = await self.session.execute(query)
            
        return result.scalars().first()

    async def get_all_by_hostname(self, hostname: str) -> List[Model]:
        query = select(self.model).filter_by(host=hostname)
        result = await self.session.execute(query)

        return list[Model](result.scalars().all())

    async def get_all(self, limit: int = 100) -> List[Model]:
        query = select(self.model).limit(limit)
        r = await self.session.execute(query)
        results = r.scalars().all()

        return [r for r in results]

    async def save(self, register: Model) -> None:
        await self.session.merge(register)
        await self.session.flush()
        print(f"[REPO] Register {register.id} updated")

