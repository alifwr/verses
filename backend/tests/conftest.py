import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.seed import seed_users

TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(bind=test_engine)

    db_session = TestSessionLocal()
    seed_users(db_session)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield db_session

    db_session.close()
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def alif_token(client):
    response = client.post("/auth/login", json={"username": "alif", "password": "verse2024"})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def syifa_token(client):
    response = client.post("/auth/login", json={"username": "syifa", "password": "verse2024"})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
