import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database_module
import app.main as main_module
from app.database import Base, get_db
from app.main import app
from app.models import User
from app.supabase_auth import get_current_user

TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Patch the engine so the app lifespan uses the test database, not production PostgreSQL
database_module.engine = test_engine
main_module.engine = test_engine


def create_test_users(db):
    alif = User(
        supabase_uid="test-uid-alif",
        email="alif@test.com",
        display_name="Alif",
    )
    syifa = User(
        supabase_uid="test-uid-syifa",
        email="syifa@test.com",
        display_name="Syifa",
    )
    db.add(alif)
    db.add(syifa)
    db.flush()
    alif.partner_id = syifa.id
    syifa.partner_id = alif.id
    db.commit()
    return alif, syifa


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(bind=test_engine)

    db_session = TestSessionLocal()
    create_test_users(db_session)

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
def alif_user(db):
    return db.query(User).filter(User.email == "alif@test.com").first()


@pytest.fixture
def syifa_user(db):
    return db.query(User).filter(User.email == "syifa@test.com").first()


@pytest.fixture
def alif_client(client, alif_user):
    """Client that is authenticated as alif."""
    app.dependency_overrides[get_current_user] = lambda: alif_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def syifa_client(client, syifa_user):
    """Client that is authenticated as syifa."""
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)
