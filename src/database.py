from typing import Optional
from src.models import A_Register, MX_Register

from sqlalchemy.sql import select
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.schema import Table, Column, MetaData
from sqlalchemy.types import Integer, String
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import registry

metadata = MetaData()

engine = create_engine('sqlite:///example.db', echo=False)

a_register_table = Table(
    'a_register',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('host', String(100)),
    Column('ip', String(100))
)

mx_register_table = Table(
    'mx_register',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('host', String(100), nullable=False),
    Column('exchange', String(100), nullable=False),
    Column('preference', Integer, nullable=False)
)


class A_RegisterRepository:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.main_register = A_Register(
            _id=0, _host='router.tim.com.', _ip='192.168.1.1'
        )

    def get(self, register_id: int) -> A_Register:
        if register_id == 0:
            return self.main_register

        query = select(A_Register).filter_by(id=register_id)
        query_result = self.__connection.execute(query)
        try:
            return query_result.scalar()
        except NoResultFound:
            return None
        
    def get_by_hostname(self, hostname: str) -> Optional[A_Register]:
        if hostname == 'router.tim.com.':
            return self.main_register

        query = select(A_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return A_Register(_id=result[0], _host=result[1], _ip=result[2])
        except NoResultFound:
            return None
        
    def save(self, a_register: A_Register) -> None:
        existing_register = self.get(a_register.id)
        
        if existing_register is None:
            insert_statement = a_register_table.insert().values(
                host=str(a_register.host),
                ip=a_register.ip
            )
            self.__connection.execute(insert_statement)
            self.__connection.commit()
            print(f'Register {a_register} saved!')
        else:
            update_statement = a_register_table.update().where(
                a_register_table.c.id == a_register.id
            ).values(
                host=str(a_register.host),
                ip=a_register.ip
            )
            self.__connection.execute(update_statement)
            self.__connection.commit()
            print(f'Register {a_register} updated!')



class MX_RegisterRepository:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection

    def get(self, register_id: int) -> MX_Register:
        if register_id == 0:
            return self.main_register

        query = select(MX_Register).filter_by(id=register_id)
        query_result = self.__connection.execute(query)
        try:
            return query_result.scalar()
        except NoResultFound:
            return None
        
    def get_by_hostname(self, hostname: str) -> Optional[A_Register]:

        query = select(MX_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None

            return MX_Register(
                _id=result[0],
                _host=result[1],
                _exchange=result[2],
                _preference=result[3]
            )

        except NoResultFound:
            return None
        
    def get_all_by_hostname(self, hostname: str) -> Optional[A_Register]:

        query = select(MX_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            results = query_result.all()

            return [MX_Register(
                _id=result[0],
                _host=result[1],
                _exchange=result[2],
                _preference=result[3]
            ) for result in results]

        except NoResultFound:
            return []
        
    def save(self, register: MX_Register) -> None:
        existing_register = self.get(register.id)
        
        if existing_register is None:
            insert_statement = mx_register_table.insert().values(
                host=str(register.host),
                exchange=str(register.exchange),
                preference=str(register.preference)
            )
            self.__connection.execute(insert_statement)
            self.__connection.commit()
            print(f'Register {register} saved!')
        else:
            update_statement = mx_register_table.update().where(
                mx_register_table.c.id == register.id
            ).values(
                host=str(register.host),
                exchange=str(register.exchange),
                preference=str(register.preference)
            )
            self.__connection.execute(update_statement)
            self.__connection.commit()
            print(f'Register {register} updated!')


def init_mappers():
    mapper_registry = registry()
    metadata.create_all(bind=engine)
    mapper_registry.map_imperatively(A_Register, a_register_table)
    mapper_registry.map_imperatively(MX_Register, mx_register_table)