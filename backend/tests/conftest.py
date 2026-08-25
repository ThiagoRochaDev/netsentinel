"""Configura um banco SQLite temporário e settings mínimas ANTES de qualquer
módulo `app.*` ser importado — db.py cria a engine no import do módulo, então
essas env vars precisam existir antes disso (conftest.py roda antes da coleta
dos testes, então isso vale mesmo se um teste só importa `app.db` no topo)."""

import os
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="netsentinel-tests-")
os.environ.setdefault("NETSENTINEL_DB_PATH", os.path.join(_tmp_dir, "test.db"))
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault(
    "ADMIN_PASSWORD_HASH",
    "$2b$12$C6UzMDM.H6dfI/f/IKcEeOgxPn2X/y3fF3sT9mS9V6c1e1e1e1e1e",
)
os.environ.setdefault("NETSENTINEL_ENV", "test")

import pytest
from sqlalchemy.orm import Session

from app.db import Base, engine, init_db


@pytest.fixture(autouse=True)
def _clean_db():
    """Recria o schema do zero antes de cada teste — testes não compartilham
    estado entre si mesmo rodando contra o mesmo arquivo sqlite."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield


@pytest.fixture
def db_session():
    from app.db import SessionLocal

    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
