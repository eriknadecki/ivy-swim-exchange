import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import models  # noqa: F401  (registers tables on Base.metadata)
from app.db.session import Base, get_db
from app.main import app

_TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/ivyswim_test"
_TABLES_IN_FK_ORDER = ["ledger_entries", "invites", "accounts", "users"]


def _ensure_test_database_exists() -> None:
    admin_engine = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'ivyswim_test'")
        ).scalar()
        if not exists:
            conn.execute(text("CREATE DATABASE ivyswim_test"))
    admin_engine.dispose()


_ensure_test_database_exists()
_test_engine = create_engine(_TEST_DATABASE_URL)
Base.metadata.create_all(_test_engine)
TestSessionLocal = sessionmaker(bind=_test_engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        for table in _TABLES_IN_FK_ORDER:
            session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        session.commit()
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
