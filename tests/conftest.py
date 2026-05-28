import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_calculus.db")

from app.database.connection import Base, engine
from app.services.seed_service import seed_database
from main import app


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    if os.path.exists("test_calculus.db"):
        os.remove("test_calculus.db")
    Base.metadata.create_all(bind=engine)
    from app.database.connection import SessionLocal

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    engine.dispose()
    if os.path.exists("test_calculus.db"):
        try:
            os.remove("test_calculus.db")
        except OSError:
            pass


@pytest.fixture
def client():
    return TestClient(app)
