import threading
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_settings = get_settings()
Path(_settings.netsentinel_db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{_settings.netsentinel_db_path}",
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
# expire_on_commit=False matters here: collectors and the alert engine
# routinely hand ORM objects (e.g. newly-created Device rows) to code that
# reads their attributes *after* the `with get_session()/get_write_session()`
# block that fetched them has already committed and closed. With the
# SQLAlchemy default (expire_on_commit=True), those attributes would be
# expired on commit and raise DetachedInstanceError on next access since
# there's no session left to re-fetch them from.

# SQLite tolerates concurrent readers fine under WAL, but concurrent writers
# from different threads/collectors can still hit "database is locked".
# Every write goes through this lock so collectors, the alert engine, and API
# writes never race each other. Reads (the API's GET endpoints) don't need it.
write_lock = threading.Lock()


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_write_session():
    with write_lock:
        with get_session() as session:
            yield session


def init_db() -> None:
    # Continua criando via create_all no boot (comportamento inalterado) — é
    # instalação self-hosted de usuário único, sem histórico de deploy a
    # preservar, então não há ganho em trocar por `alembic upgrade head` aqui.
    # A migração baseline em alembic/versions/ existe pra registrar o schema
    # atual e servir de ponto de partida: qualquer mudança de schema *daqui
    # pra frente* deve virar uma revisão Alembic (`alembic revision
    # --autogenerate`), não um ajuste direto no create_all.
    from app import models  # noqa: F401  (ensures models are registered)

    Base.metadata.create_all(bind=engine)
