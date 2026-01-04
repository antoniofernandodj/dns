# src/repositories/repository_factory.py


from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import (
    A_RegisterRepository,
    AAAA_RegisterRepository,
    CNAME_RegisterRepository,
    MX_RegisterRepository,
    NS_RegisterRepository,
    SOA_RegisterRepository,
    SRV_RegisterRepository,
    TXT_RegisterRepository,
)


# Factory pattern para criar repositórios
class RepositoryFactory:
    """
    Factory para criar repositórios compartilhando a mesma conexão.
    Evita criar múltiplas instâncias do mesmo repositório.
    """

    def __init__(self, session: AsyncSession):
        self._session = session
        self._a_repository: A_RegisterRepository | None = None
        self._mx_repository: MX_RegisterRepository | None = None
        self._aaaa_repository: AAAA_RegisterRepository | None = None
        self._cname_repository: CNAME_RegisterRepository | None = None
        self._txt_repository: TXT_RegisterRepository | None = None
        self._ns_repository: NS_RegisterRepository | None = None
        self._soa_repository: SOA_RegisterRepository | None = None
        self._srv_repository: SRV_RegisterRepository | None = None

    @property
    def a_repository(self) -> A_RegisterRepository:
        if self._a_repository is None:
            self._a_repository = A_RegisterRepository(self._session)
        return self._a_repository

    @property
    def mx_repository(self) -> MX_RegisterRepository:
        if self._mx_repository is None:
            self._mx_repository = MX_RegisterRepository(self._session)
        return self._mx_repository

    @property
    def aaaa_repository(self) -> AAAA_RegisterRepository:
        if self._aaaa_repository is None:
            self._aaaa_repository = AAAA_RegisterRepository(self._session)
        return self._aaaa_repository

    @property
    def cname_repository(self) -> CNAME_RegisterRepository:
        if self._cname_repository is None:
            self._cname_repository = CNAME_RegisterRepository(self._session)
        return self._cname_repository

    @property
    def txt_repository(self) -> TXT_RegisterRepository:
        if self._txt_repository is None:
            self._txt_repository = TXT_RegisterRepository(self._session)
        return self._txt_repository

    @property
    def ns_repository(self) -> NS_RegisterRepository:
        if self._ns_repository is None:
            self._ns_repository = NS_RegisterRepository(self._session)
        return self._ns_repository

    @property
    def soa_repository(self) -> SOA_RegisterRepository:
        if self._soa_repository is None:
            self._soa_repository = SOA_RegisterRepository(self._session)
        return self._soa_repository

    @property
    def srv_repository(self) -> SRV_RegisterRepository:
        if self._srv_repository is None:
            self._srv_repository = SRV_RegisterRepository(self._session)
        return self._srv_repository

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()

    async def close(self):
        await self._session.close()
