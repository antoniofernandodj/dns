from src.models import (
    A_Register,
    MX_Register,
    AAAA_Register,
    CNAME_Register,
    TXT_Register,
    NS_Register,
    SOA_Register,
    SRV_Register,
)

from typing import Optional, List

from sqlalchemy.sql import select
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.schema import Table, Column, MetaData
from sqlalchemy.types import Integer, String
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import registry


from src.database import (
    a_register_table,
    mx_register_table,
    aaaa_register_table,
    cname_register_table,
    txt_register_table,
    ns_register_table,
    soa_register_table,
    srv_register_table,
)


class A_RegisterRepository:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.model = A_Register
        self.main_register = A_Register(
            _id=0, _host="router.tim.com.", _ip="192.168.1.1"
        )

    def get(self, register_id: int) -> Optional[A_Register]:
        if register_id == 0:
            return self.main_register

        query = select(self.model).filter_by(id=register_id)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return A_Register(_id=result[0], _host=result[1], _ip=result[2])
        except NoResultFound:
            return None

    def get_by_hostname(self, hostname: str) -> Optional[A_Register]:
        if hostname == "router.tim.com.":
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
        if a_register.id is None:
            raise AttributeError

        existing_register = self.get(a_register.id)

        if existing_register is None:
            insert_statement = a_register_table.insert().values(
                host=str(a_register.host), ip=a_register.ip
            )
            self.__connection.execute(insert_statement)
            self.__connection.commit()
            print(f"Register {a_register} saved!")
        else:
            update_statement = (
                a_register_table.update()
                .where(a_register_table.c.id == a_register.id)
                .values(host=str(a_register.host), ip=a_register.ip)
            )
            self.__connection.execute(update_statement)
            self.__connection.commit()
            print(f"Register {a_register} updated!")


class MX_RegisterRepository:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.model = MX_Register

    def get(self, register_id: int) -> Optional[MX_Register]:

        query = select(self.model).filter_by(id=register_id)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return MX_Register(
                _id=result[0],
                _host=result[1],
                _exchange=result[2],
                _preference=result[3],
            )
        except NoResultFound:
            return None

    def get_by_hostname(self, hostname: str) -> Optional[MX_Register]:

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
                _preference=result[3],
            )

        except NoResultFound:
            return None

    def get_all_by_hostname(self, hostname: str) -> List[MX_Register]:

        query = select(MX_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            results = query_result.all()

            return [
                MX_Register(
                    _id=result[0],
                    _host=result[1],
                    _exchange=result[2],
                    _preference=result[3],
                )
                for result in results
            ]

        except NoResultFound:
            return []

    def save(self, register: MX_Register) -> None:
        if register.id is None:
            raise AttributeError

        existing_register = self.get(register.id)

        if existing_register is None:
            insert_statement = mx_register_table.insert().values(
                host=str(register.host),
                exchange=str(register.exchange),
                preference=str(register.preference),
            )
            self.__connection.execute(insert_statement)
            self.__connection.commit()
            print(f"Register {register} saved!")
        else:
            update_statement = (
                mx_register_table.update()
                .where(mx_register_table.c.id == register.id)
                .values(
                    host=str(register.host),
                    exchange=str(register.exchange),
                    preference=str(register.preference),
                )
            )
            self.__connection.execute(update_statement)
            self.__connection.commit()
            print(f"Register {register} updated!")


class AAAA_RegisterRepository:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.model = AAAA_Register

    def get(self, register_id: int) -> Optional[AAAA_Register]:

        query = select(self.model).filter_by(id=register_id)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return AAAA_Register(_id=result[0], _host=result[1], _ip=result[2])
        except NoResultFound:
            return None

    def get_by_hostname(self, hostname: str) -> Optional[AAAA_Register]:
        query = select(AAAA_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return AAAA_Register(_id=result[0], _host=result[1], _ip=result[2])
        except NoResultFound:
            return None

    def save(self, register: AAAA_Register) -> None:
        if register.id is None:
            raise AttributeError

        existing_register = self.get(register.id)
        if existing_register is None:
            insert_statement = aaaa_register_table.insert().values(
                host=str(register.host), ip=register.ip
            )
            self.__connection.execute(insert_statement)
            self.__connection.commit()
            print(f"Register {register} saved!")
        else:
            update_statement = (
                aaaa_register_table.update()
                .where(aaaa_register_table.c.id == register.id)
                .values(host=str(register.host), ip=register.ip)
            )
            self.__connection.execute(update_statement)
            self.__connection.commit()
            print(f"Register {register} updated!")


class CNAME_RegisterRepository:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.model = CNAME_Register

    def get(self, register_id: int) -> Optional[CNAME_Register]:

        query = select(self.model).filter_by(id=register_id)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return CNAME_Register(
                _id=result[0], _host=result[1], _canonical_name=result[2]
            )
        except NoResultFound:
            return None

    def get_by_hostname(self, hostname: str) -> Optional[CNAME_Register]:
        query = select(CNAME_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return CNAME_Register(
                _id=result[0], _host=result[1], _canonical_name=result[2]
            )
        except NoResultFound:
            return None

    def save(self, register: CNAME_Register) -> None:
        if register.id is None:
            raise AttributeError

        existing_register = self.get(register.id)
        if existing_register is None:
            insert_statement = cname_register_table.insert().values(
                host=str(register.host), canonical_name=str(register.canonical_name)
            )
            self.__connection.execute(insert_statement)
            self.__connection.commit()
            print(f"Register {register} saved!")
        else:
            update_statement = (
                cname_register_table.update()
                .where(cname_register_table.c.id == register.id)
                .values(
                    host=str(register.host), canonical_name=str(register.canonical_name)
                )
            )
            self.__connection.execute(update_statement)
            self.__connection.commit()
            print(f"Register {register} updated!")


class TXT_RegisterRepository:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.model = TXT_Register

    def get(self, register_id: int) -> Optional[TXT_Register]:

        query = select(self.model).filter_by(id=register_id)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return TXT_Register(_id=result[0], _host=result[1], _text=result[2])
        except NoResultFound:
            return None

    def get_by_hostname(self, hostname: str) -> Optional[TXT_Register]:
        query = select(TXT_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return TXT_Register(_id=result[0], _host=result[1], _text=result[2])
        except NoResultFound:
            return None

    def get_all_by_hostname(self, hostname: str) -> List[TXT_Register]:
        query = select(TXT_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            results = query_result.all()
            return [
                TXT_Register(_id=result[0], _host=result[1], _text=result[2])
                for result in results
            ]
        except NoResultFound:
            return []

    def save(self, register: TXT_Register) -> None:
        if register.id is None:
            raise AttributeError

        existing_register = self.get(register.id)
        if existing_register is None:
            insert_statement = txt_register_table.insert().values(
                host=str(register.host), text=str(register.text)
            )
            self.__connection.execute(insert_statement)
            self.__connection.commit()
            print(f"Register {register} saved!")
        else:
            update_statement = (
                txt_register_table.update()
                .where(txt_register_table.c.id == register.id)
                .values(host=str(register.host), text=str(register.text))
            )
            self.__connection.execute(update_statement)
            self.__connection.commit()
            print(f"Register {register} updated!")


class NS_RegisterRepository:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.model = NS_Register

    def get(self, register_id: int) -> Optional[NS_Register]:

        query = select(self.model).filter_by(id=register_id)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return NS_Register(_id=result[0], _host=result[1], _nameserver=result[2])
        except NoResultFound:
            return None

    def get_by_hostname(self, hostname: str) -> Optional[NS_Register]:
        query = select(NS_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return NS_Register(_id=result[0], _host=result[1], _nameserver=result[2])
        except NoResultFound:
            return None

    def save(self, register: NS_Register) -> None:
        if register.id is None:
            raise AttributeError

        existing_register = self.get(register.id)
        if existing_register is None:
            insert_statement = ns_register_table.insert().values(
                host=str(register.host), nameserver=str(register.nameserver)
            )
            self.__connection.execute(insert_statement)
            self.__connection.commit()
            print(f"Register {register} saved!")
        else:
            update_statement = (
                ns_register_table.update()
                .where(ns_register_table.c.id == register.id)
                .values(host=str(register.host), nameserver=str(register.nameserver))
            )
            self.__connection.execute(update_statement)
            self.__connection.commit()
            print(f"Register {register} updated!")


class SOA_RegisterRepository:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.model = SOA_Register

    def get(self, register_id: int) -> Optional[SOA_Register]:

        query = select(self.model).filter_by(id=register_id)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return SOA_Register(
                _id=result[0],
                _host=result[1],
                _mname=result[2],
                _rname=result[3],
                _serial=result[4],
                _refresh=result[5],
                _retry=result[6],
                _expire=result[7],
                _minimum=result[8],
            )
        except NoResultFound:
            return None

    def get_by_hostname(self, hostname: str) -> Optional[SOA_Register]:
        query = select(SOA_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return SOA_Register(
                _id=result[0],
                _host=result[1],
                _mname=result[2],
                _rname=result[3],
                _serial=result[4],
                _refresh=result[5],
                _retry=result[6],
                _expire=result[7],
                _minimum=result[8],
            )
        except NoResultFound:
            return None

    def save(self, register: SOA_Register) -> None:
        if register.id is None:
            raise AttributeError

        existing_register = self.get(register.id)
        if existing_register is None:
            insert_statement = soa_register_table.insert().values(
                host=str(register.host),
                mname=str(register.mname),
                rname=str(register.rname),
                serial=register.serial,
                refresh=register.refresh,
                retry=register.retry,
                expire=register.expire,
                minimum=register.minimum,
            )
            self.__connection.execute(insert_statement)
            self.__connection.commit()
            print(f"Register {register} saved!")
        else:
            update_statement = (
                soa_register_table.update()
                .where(soa_register_table.c.id == register.id)
                .values(
                    host=str(register.host),
                    mname=str(register.mname),
                    rname=str(register.rname),
                    serial=register.serial,
                    refresh=register.refresh,
                    retry=register.retry,
                    expire=register.expire,
                    minimum=register.minimum,
                )
            )
            self.__connection.execute(update_statement)
            self.__connection.commit()
            print(f"Register {register} updated!")


class SRV_RegisterRepository:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection
        self.model = SRV_Register

    def get(self, register_id: int) -> Optional[SRV_Register]:

        query = select(self.model).filter_by(id=register_id)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return SRV_Register(
                _id=result[0],
                _host=result[1],
                _target=result[2],
                _port=result[3],
                _weight=result[4],
                _priority=result[5],
            )
        except NoResultFound:
            return None

    def get_by_hostname(self, hostname: str) -> Optional[SRV_Register]:
        query = select(SRV_Register).filter_by(host=hostname)
        query_result = self.__connection.execute(query)
        try:
            result = query_result.first()
            if result is None:
                return None
            return SRV_Register(
                _id=result[0],
                _host=result[1],
                _target=result[2],
                _port=result[3],
                _weight=result[4],
                _priority=result[5],
            )
        except NoResultFound:
            return None

    def save(self, register: SRV_Register) -> None:
        if register.id is None:
            raise AttributeError

        existing_register = self.get(register.id)
        if existing_register is None:
            insert_statement = srv_register_table.insert().values(
                host=str(register.host),
                target=str(register.target),
                port=register.port,
                weight=register.weight,
                priority=register.priority,
            )
            self.__connection.execute(insert_statement)
            self.__connection.commit()
            print(f"Register {register} saved!")
        else:
            update_statement = (
                srv_register_table.update()
                .where(srv_register_table.c.id == register.id)
                .values(
                    host=str(register.host),
                    target=str(register.target),
                    port=register.port,
                    weight=register.weight,
                    priority=register.priority,
                )
            )
            self.__connection.execute(update_statement)
            self.__connection.commit()
            print(f"Register {register} updated!")
