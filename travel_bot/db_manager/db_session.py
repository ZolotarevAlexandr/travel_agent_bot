import logging
import os

import sqlalchemy as sa
import sqlalchemy.ext.declarative as dec
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)

SqlAlchemyBase = dec.declarative_base()
__factory = None


def global_init():
    global __factory

    if __factory:
        return

    conn_str = os.getenv("DB_URL")
    logger.info(f"Connecting to db: {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models  # noqa

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
