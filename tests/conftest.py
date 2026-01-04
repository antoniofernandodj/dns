import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


# test_config.py

import pytest
from sqlalchemy.orm import sessionmaker

from src.database import engine as __engine


@pytest.fixture(scope="module")
async def engine():

    return __engine


@pytest.fixture(scope="module")
def connection(engine):
    connection = engine.connect()

    yield connection
    connection.close()


@pytest.fixture(scope="function")
def session(connection):
    # Cria uma nova sessão para cada teste
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
