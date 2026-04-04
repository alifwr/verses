# Verse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Verse, a collaborative relationship management app with Ledger, Inquiry Hub, and Marriage Roadmap modules, secured by JWT auth and a digital curfew system.

**Architecture:** FastAPI backend with SQLAlchemy ORM and SQLite, serving a Nuxt 4 frontend with Tailwind CSS. Two pre-seeded users (alif/syifa) with JWT-based auth. Backend in `backend/`, frontend in `frontend/`.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy, python-jose, passlib, Nuxt 4, Tailwind CSS, TypeScript

---

## File Structure

### Backend (`backend/`)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, router mounting
│   ├── config.py             # Settings (SECRET_KEY, DB_URL, token expiry)
│   ├── database.py           # SQLAlchemy engine, session, Base
│   ├── models.py             # All SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── auth.py               # JWT creation, password hashing, get_current_user
│   ├── seed.py               # Pre-seed alif and syifa
│   ├── middleware.py          # Adab curfew middleware
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py           # /auth/login, /auth/refresh, /auth/me
│   │   ├── rules.py          # /rules CRUD + sign
│   │   ├── questions.py      # /questions CRUD + answer + double-blind
│   │   └── milestones.py     # /milestones CRUD + approve
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Test client, test DB, fixtures
│   ├── test_auth.py
│   ├── test_rules.py
│   ├── test_questions.py
│   ├── test_milestones.py
│   └── test_curfew.py
├── requirements.txt
└── verse.db                  # Created at runtime (gitignored)
```

### Frontend (`frontend/`)

```
frontend/
├── nuxt.config.ts
├── package.json
├── tailwind.config.ts
├── app.vue                   # Root app shell
├── assets/
│   └── css/
│       └── main.css          # Tailwind directives + custom styles
├── composables/
│   ├── useAuth.ts            # JWT auth composable
│   └── useApi.ts             # API fetch wrapper with auth header
├── middleware/
│   └── auth.global.ts        # Route guard
├── layouts/
│   └── default.vue           # App layout with nav
├── pages/
│   ├── login.vue
│   ├── ledger.vue
│   ├── inquiry.vue
│   └── roadmap.vue
├── components/
│   ├── NavBar.vue
│   ├── RuleCard.vue
│   ├── QuestionCard.vue
│   ├── MilestoneCard.vue
│   ├── MountainBackground.vue
│   └── EmergencyOverrideModal.vue
└── server/
    └── api/                  # (empty - API proxied to FastAPI)
```

---

## Task 1: Backend Project Setup & Database

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/app/seed.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
pytest==8.3.0
httpx==0.27.0
```

- [ ] **Step 2: Install dependencies**

```bash
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

- [ ] **Step 3: Create config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "verse-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite:///./verse.db"


settings = Settings()
```

- [ ] **Step 4: Create database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5: Create models.py**

```python
from datetime import datetime, date
from sqlalchemy import Integer, String, Text, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))
    partner_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    partner: Mapped["User | None"] = relationship("User", remote_side=[id], foreign_keys=[partner_id])


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    user: Mapped[User] = relationship("User")


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    proposed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    is_sealed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    proposer: Mapped[User] = relationship("User", foreign_keys=[proposed_by])
    signatures: Mapped[list["RuleSignature"]] = relationship("RuleSignature", back_populates="rule", cascade="all, delete-orphan")


class RuleSignature(Base):
    __tablename__ = "rule_signatures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("rules.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    signed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    rule: Mapped[Rule] = relationship("Rule", back_populates="signatures")
    user: Mapped[User] = relationship("User")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(Text)
    asked_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asker: Mapped[User] = relationship("User", foreign_keys=[asked_by])
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    question: Mapped[Question] = relationship("Question", back_populates="answers")
    user: Mapped[User] = relationship("User")


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    proposed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    proposer: Mapped[User] = relationship("User", foreign_keys=[proposed_by])
    approvals: Mapped[list["MilestoneApproval"]] = relationship("MilestoneApproval", back_populates="milestone", cascade="all, delete-orphan")


class MilestoneApproval(Base):
    __tablename__ = "milestone_approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    milestone_id: Mapped[int] = mapped_column(Integer, ForeignKey("milestones.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    approved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    milestone: Mapped[Milestone] = relationship("Milestone", back_populates="approvals")
    user: Mapped[User] = relationship("User")
```

- [ ] **Step 6: Create seed.py**

```python
from passlib.context import CryptContext
from sqlalchemy.orm import Session as DBSession

from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_users(db: DBSession) -> None:
    existing = db.query(User).first()
    if existing:
        return

    alif = User(
        username="alif",
        display_name="Alif",
        hashed_password=pwd_context.hash("verse2024"),
        is_online=False,
    )
    syifa = User(
        username="syifa",
        display_name="Syifa",
        hashed_password=pwd_context.hash("verse2024"),
        is_online=False,
    )
    db.add(alif)
    db.add(syifa)
    db.flush()

    alif.partner_id = syifa.id
    syifa.partner_id = alif.id
    db.commit()
```

- [ ] **Step 7: Create main.py (minimal)**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, SessionLocal
from app.seed import seed_users

app = FastAPI(title="Verse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 8: Create conftest.py with test fixtures**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.seed import seed_users

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_users(db)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(db):
    return TestClient(app)


@pytest.fixture
def alif_token(client):
    resp = client.post("/auth/login", data={"username": "alif", "password": "verse2024"})
    return resp.json()["access_token"]


@pytest.fixture
def syifa_token(client):
    resp = client.post("/auth/login", data={"username": "syifa", "password": "verse2024"})
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
```

- [ ] **Step 9: Create __init__.py files**

Empty `backend/app/__init__.py`, `backend/app/routes/__init__.py`, `backend/tests/__init__.py`.

- [ ] **Step 10: Run health check test**

```bash
cd backend && source venv/bin/activate && python -c "from app.main import app; print('Import OK')"
```

Expected: `Import OK`

- [ ] **Step 11: Commit**

```bash
git add backend/
git commit -m "feat(backend): project setup with models, database, and seed data"
```

---

## Task 2: Backend Auth (JWT + Login + Me)

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/auth.py`
- Create: `backend/app/routes/auth.py`
- Modify: `backend/app/main.py` (mount auth router)
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Write auth tests**

```python
from tests.conftest import auth_header


def test_login_success(client):
    resp = client.post("/auth/login", data={"username": "alif", "password": "verse2024"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    resp = client.post("/auth/login", data={"username": "alif", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post("/auth/login", data={"username": "unknown", "password": "verse2024"})
    assert resp.status_code == 401


def test_me_authenticated(client, alif_token):
    resp = client.get("/auth/me", headers=auth_header(alif_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alif"
    assert data["display_name"] == "Alif"
    assert "partner" in data


def test_me_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_refresh_token(client, alif_token):
    login_resp = client.post("/auth/login", data={"username": "alif", "password": "verse2024"})
    refresh = login_resp.json()["refresh_token"]
    resp = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
```

- [ ] **Step 2: Create schemas.py**

```python
from datetime import date, datetime
from pydantic import BaseModel


# Auth
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PartnerInfo(BaseModel):
    id: int
    username: str
    display_name: str
    is_online: bool


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    partner: PartnerInfo | None = None

    class Config:
        from_attributes = True


# Rules
class RuleCreate(BaseModel):
    title: str
    description: str
    emergency_override: bool = False


class RuleOut(BaseModel):
    id: int
    title: str
    description: str
    proposed_by: int
    proposer_name: str
    is_sealed: bool
    is_agreed_by_me: bool
    is_agreed_by_partner: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Questions
class QuestionCreate(BaseModel):
    text: str
    emergency_override: bool = False


class AnswerCreate(BaseModel):
    text: str
    emergency_override: bool = False


class AnswerOut(BaseModel):
    id: int
    user_id: int
    username: str
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    id: int
    text: str
    asked_by: int
    asker_name: str
    my_answer: AnswerOut | None = None
    partner_answer: AnswerOut | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# Milestones
class MilestoneCreate(BaseModel):
    title: str
    description: str
    target_date: date | None = None


class MilestoneUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    target_date: date | None = None
    is_completed: bool | None = None


class MilestoneOut(BaseModel):
    id: int
    title: str
    description: str
    target_date: date | None
    proposed_by: int
    proposer_name: str
    is_confirmed: bool
    is_completed: bool
    is_approved_by_me: bool
    is_approved_by_partner: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 3: Create auth.py**

```python
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session as DBSession

from app.config import settings
from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
```

- [ ] **Step 4: Create routes/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session as DBSession

from app.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_password,
)
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import PartnerInfo, Token, TokenOut, TokenRefresh, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    user.is_online = True
    db.commit()
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenOut)
def refresh(body: TokenRefresh, db: DBSession = Depends(get_db)):
    try:
        payload = jwt.decode(body.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if username is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    new_access = create_access_token(data={"sub": user.username})
    return TokenOut(access_token=new_access)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    partner = db.query(User).filter(User.id == current_user.partner_id).first()
    partner_info = None
    if partner:
        partner_info = PartnerInfo(
            id=partner.id,
            username=partner.username,
            display_name=partner.display_name,
            is_online=partner.is_online,
        )
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        partner=partner_info,
    )
```

- [ ] **Step 5: Mount auth router in main.py**

Add to `main.py` after app creation:

```python
from app.routes.auth import router as auth_router

app.include_router(auth_router)
```

- [ ] **Step 6: Run auth tests**

```bash
cd backend && source venv/bin/activate && pytest tests/test_auth.py -v
```

Expected: All 6 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat(backend): JWT auth with login, refresh, and me endpoints"
```

---

## Task 3: Backend Adab Middleware (Curfew)

**Files:**
- Create: `backend/app/middleware.py`
- Modify: `backend/app/main.py` (add middleware)
- Create: `backend/tests/test_curfew.py`

- [ ] **Step 1: Write curfew tests**

```python
from unittest.mock import patch
from datetime import datetime
from tests.conftest import auth_header


def test_write_allowed_during_day(client, alif_token):
    with patch("app.middleware.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 4, 14, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        resp = client.post(
            "/rules",
            json={"title": "Test Rule", "description": "Test"},
            headers=auth_header(alif_token),
        )
        assert resp.status_code != 403


def test_write_blocked_during_curfew(client, alif_token):
    with patch("app.middleware.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 4, 22, 30, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        resp = client.post(
            "/rules",
            json={"title": "Test Rule", "description": "Test"},
            headers=auth_header(alif_token),
        )
        assert resp.status_code == 403
        assert "curfew" in resp.json()["detail"].lower()


def test_write_allowed_with_emergency_override(client, alif_token):
    with patch("app.middleware.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 4, 23, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        resp = client.post(
            "/rules",
            json={"title": "Emergency", "description": "Urgent", "emergency_override": True},
            headers=auth_header(alif_token),
        )
        assert resp.status_code != 403


def test_get_allowed_during_curfew(client, alif_token):
    with patch("app.middleware.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 4, 23, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        resp = client.get("/rules", headers=auth_header(alif_token))
        assert resp.status_code != 403
```

- [ ] **Step 2: Create middleware.py**

```python
from datetime import datetime

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseCall
from starlette.responses import Response
import json


CURFEW_PATHS = ["/rules", "/questions"]


class AdabCurfewMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseCall) -> Response:
        if request.method == "GET":
            return await call_next(request)

        path = request.url.path
        is_curfew_path = any(path.startswith(p) for p in CURFEW_PATHS)

        if not is_curfew_path:
            return await call_next(request)

        now = datetime.now()
        hour = now.hour
        is_curfew = hour >= 22 or hour < 4

        if not is_curfew:
            return await call_next(request)

        # Check emergency override in body
        try:
            body = await request.body()
            if body:
                data = json.loads(body)
                if data.get("emergency_override") is True:
                    # Reconstruct request with body since we consumed it
                    return await call_next(request)
        except (json.JSONDecodeError, Exception):
            pass

        raise HTTPException(
            status_code=403,
            detail="Adab Curfew: Non-GET requests to Ledger and Inquiry are restricted between 10:00 PM and 4:00 AM.",
        )
```

- [ ] **Step 3: Mount middleware in main.py**

Add to `main.py`:

```python
from app.middleware import AdabCurfewMiddleware

app.add_middleware(AdabCurfewMiddleware)
```

- [ ] **Step 4: Run curfew tests**

```bash
cd backend && source venv/bin/activate && pytest tests/test_curfew.py -v
```

Expected: All 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(backend): Adab curfew middleware (10PM-4AM write restriction)"
```

---

## Task 4: Backend Rules (Ledger) Endpoints

**Files:**
- Create: `backend/app/routes/rules.py`
- Modify: `backend/app/main.py` (mount router)
- Create: `backend/tests/test_rules.py`

- [ ] **Step 1: Write rules tests**

```python
from tests.conftest import auth_header


def test_create_rule(client, alif_token):
    resp = client.post(
        "/rules",
        json={"title": "No late calls", "description": "Calls end by 9 PM"},
        headers=auth_header(alif_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "No late calls"
    assert data["is_sealed"] is False
    assert data["is_agreed_by_me"] is False
    assert data["is_agreed_by_partner"] is False


def test_list_rules(client, alif_token):
    client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    resp = client.get("/rules", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_sign_rule(client, alif_token, syifa_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]

    # Alif signs
    resp = client.post(f"/rules/{rule_id}/sign", headers=auth_header(alif_token))
    assert resp.status_code == 200

    # Check from alif's perspective
    resp = client.get("/rules", headers=auth_header(alif_token))
    rule = [r for r in resp.json() if r["id"] == rule_id][0]
    assert rule["is_agreed_by_me"] is True
    assert rule["is_agreed_by_partner"] is False
    assert rule["is_sealed"] is False

    # Syifa signs -> sealed
    resp = client.post(f"/rules/{rule_id}/sign", headers=auth_header(syifa_token))
    assert resp.status_code == 200

    resp = client.get("/rules", headers=auth_header(alif_token))
    rule = [r for r in resp.json() if r["id"] == rule_id][0]
    assert rule["is_sealed"] is True


def test_delete_rule_by_proposer(client, alif_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    resp = client.delete(f"/rules/{rule_id}", headers=auth_header(alif_token))
    assert resp.status_code == 200


def test_cannot_delete_sealed_rule(client, alif_token, syifa_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    client.post(f"/rules/{rule_id}/sign", headers=auth_header(alif_token))
    client.post(f"/rules/{rule_id}/sign", headers=auth_header(syifa_token))
    resp = client.delete(f"/rules/{rule_id}", headers=auth_header(alif_token))
    assert resp.status_code == 400


def test_cannot_delete_rule_by_non_proposer(client, alif_token, syifa_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    resp = client.delete(f"/rules/{rule_id}", headers=auth_header(syifa_token))
    assert resp.status_code == 403
```

- [ ] **Step 2: Create routes/rules.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Rule, RuleSignature, User
from app.schemas import RuleCreate, RuleOut

router = APIRouter(prefix="/rules", tags=["rules"])


def rule_to_out(rule: Rule, current_user_id: int, partner_id: int) -> RuleOut:
    signer_ids = {s.user_id for s in rule.signatures}
    return RuleOut(
        id=rule.id,
        title=rule.title,
        description=rule.description,
        proposed_by=rule.proposed_by,
        proposer_name=rule.proposer.display_name,
        is_sealed=rule.is_sealed,
        is_agreed_by_me=current_user_id in signer_ids,
        is_agreed_by_partner=partner_id in signer_ids,
        created_at=rule.created_at,
    )


@router.get("", response_model=list[RuleOut])
def list_rules(
    current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)
):
    rules = db.query(Rule).order_by(Rule.created_at.desc()).all()
    return [rule_to_out(r, current_user.id, current_user.partner_id) for r in rules]


@router.post("", response_model=RuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: RuleCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    rule = Rule(
        title=body.title,
        description=body.description,
        proposed_by=current_user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule_to_out(rule, current_user.id, current_user.partner_id)


@router.post("/{rule_id}/sign", response_model=RuleOut)
def sign_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    existing = (
        db.query(RuleSignature)
        .filter(RuleSignature.rule_id == rule_id, RuleSignature.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already signed")

    sig = RuleSignature(rule_id=rule_id, user_id=current_user.id)
    db.add(sig)
    db.flush()

    signer_count = db.query(RuleSignature).filter(RuleSignature.rule_id == rule_id).count()
    if signer_count >= 2:
        rule.is_sealed = True

    db.commit()
    db.refresh(rule)
    return rule_to_out(rule, current_user.id, current_user.partner_id)


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if rule.proposed_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the proposer can delete this rule")
    if rule.is_sealed:
        raise HTTPException(status_code=400, detail="Cannot delete a sealed rule")

    db.delete(rule)
    db.commit()
    return {"detail": "Rule deleted"}
```

- [ ] **Step 3: Mount rules router in main.py**

```python
from app.routes.rules import router as rules_router

app.include_router(rules_router)
```

- [ ] **Step 4: Run rules tests**

```bash
cd backend && source venv/bin/activate && pytest tests/test_rules.py -v
```

Expected: All 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(backend): rules/ledger endpoints with seal and sign"
```

---

## Task 5: Backend Questions (Inquiry Hub) Endpoints

**Files:**
- Create: `backend/app/routes/questions.py`
- Modify: `backend/app/main.py` (mount router)
- Create: `backend/tests/test_questions.py`

- [ ] **Step 1: Write questions tests**

```python
from tests.conftest import auth_header


def test_create_question(client, alif_token):
    resp = client.post(
        "/questions",
        json={"text": "Where should we live?"},
        headers=auth_header(alif_token),
    )
    assert resp.status_code == 201
    assert resp.json()["text"] == "Where should we live?"


def test_list_questions(client, alif_token):
    client.post("/questions", json={"text": "Q1"}, headers=auth_header(alif_token))
    resp = client.get("/questions", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_double_blind_hides_partner_answer(client, alif_token, syifa_token):
    create = client.post("/questions", json={"text": "Q1"}, headers=auth_header(alif_token))
    qid = create.json()["id"]

    # Syifa answers
    client.post(f"/questions/{qid}/answer", json={"text": "Syifa's answer"}, headers=auth_header(syifa_token))

    # Alif checks - should NOT see Syifa's answer (hasn't answered yet)
    resp = client.get(f"/questions/{qid}", headers=auth_header(alif_token))
    data = resp.json()
    assert data["my_answer"] is None
    assert data["partner_answer"] is None  # Hidden!


def test_double_blind_reveals_after_both_answer(client, alif_token, syifa_token):
    create = client.post("/questions", json={"text": "Q1"}, headers=auth_header(alif_token))
    qid = create.json()["id"]

    client.post(f"/questions/{qid}/answer", json={"text": "Syifa's answer"}, headers=auth_header(syifa_token))
    client.post(f"/questions/{qid}/answer", json={"text": "Alif's answer"}, headers=auth_header(alif_token))

    # Now Alif should see both
    resp = client.get(f"/questions/{qid}", headers=auth_header(alif_token))
    data = resp.json()
    assert data["my_answer"]["text"] == "Alif's answer"
    assert data["partner_answer"]["text"] == "Syifa's answer"


def test_cannot_answer_twice(client, alif_token):
    create = client.post("/questions", json={"text": "Q1"}, headers=auth_header(alif_token))
    qid = create.json()["id"]
    client.post(f"/questions/{qid}/answer", json={"text": "A1"}, headers=auth_header(alif_token))
    resp = client.post(f"/questions/{qid}/answer", json={"text": "A2"}, headers=auth_header(alif_token))
    assert resp.status_code == 400
```

- [ ] **Step 2: Create routes/questions.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Answer, Question, User
from app.schemas import AnswerCreate, AnswerOut, QuestionCreate, QuestionOut

router = APIRouter(prefix="/questions", tags=["questions"])


def question_to_out(question: Question, current_user_id: int, partner_id: int) -> QuestionOut:
    my_answer = None
    partner_answer = None

    for a in question.answers:
        if a.user_id == current_user_id:
            my_answer = AnswerOut(
                id=a.id, user_id=a.user_id, username=a.user.username, text=a.text, created_at=a.created_at
            )
        elif a.user_id == partner_id:
            partner_answer = AnswerOut(
                id=a.id, user_id=a.user_id, username=a.user.username, text=a.text, created_at=a.created_at
            )

    # Double-blind: hide partner answer if I haven't answered
    if my_answer is None:
        partner_answer = None

    return QuestionOut(
        id=question.id,
        text=question.text,
        asked_by=question.asked_by,
        asker_name=question.asker.display_name,
        my_answer=my_answer,
        partner_answer=partner_answer,
        created_at=question.created_at,
    )


@router.get("", response_model=list[QuestionOut])
def list_questions(
    current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)
):
    questions = db.query(Question).order_by(Question.created_at.desc()).all()
    return [question_to_out(q, current_user.id, current_user.partner_id) for q in questions]


@router.post("", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(
    body: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    question = Question(text=body.text, asked_by=current_user.id)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question_to_out(question, current_user.id, current_user.partner_id)


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question_to_out(question, current_user.id, current_user.partner_id)


@router.post("/{question_id}/answer", response_model=QuestionOut)
def answer_question(
    question_id: int,
    body: AnswerCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    existing = (
        db.query(Answer)
        .filter(Answer.question_id == question_id, Answer.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already answered this question")

    answer = Answer(question_id=question_id, user_id=current_user.id, text=body.text)
    db.add(answer)
    db.commit()
    db.refresh(question)
    return question_to_out(question, current_user.id, current_user.partner_id)
```

- [ ] **Step 3: Mount questions router in main.py**

```python
from app.routes.questions import router as questions_router

app.include_router(questions_router)
```

- [ ] **Step 4: Run questions tests**

```bash
cd backend && source venv/bin/activate && pytest tests/test_questions.py -v
```

Expected: All 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(backend): inquiry hub with double-blind answer logic"
```

---

## Task 6: Backend Milestones (Roadmap) Endpoints

**Files:**
- Create: `backend/app/routes/milestones.py`
- Modify: `backend/app/main.py` (mount router)
- Create: `backend/tests/test_milestones.py`

- [ ] **Step 1: Write milestones tests**

```python
from tests.conftest import auth_header


def test_create_milestone(client, alif_token):
    resp = client.post(
        "/milestones",
        json={"title": "Get engaged", "description": "Propose formally", "target_date": "2027-01-01"},
        headers=auth_header(alif_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Get engaged"
    assert data["is_confirmed"] is False


def test_list_milestones(client, alif_token):
    client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    resp = client.get("/milestones", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_approve_milestone_mutual(client, alif_token, syifa_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]

    client.post(f"/milestones/{mid}/approve", headers=auth_header(alif_token))
    resp = client.get("/milestones", headers=auth_header(alif_token))
    m = [x for x in resp.json() if x["id"] == mid][0]
    assert m["is_approved_by_me"] is True
    assert m["is_confirmed"] is False

    client.post(f"/milestones/{mid}/approve", headers=auth_header(syifa_token))
    resp = client.get("/milestones", headers=auth_header(alif_token))
    m = [x for x in resp.json() if x["id"] == mid][0]
    assert m["is_confirmed"] is True


def test_update_milestone(client, alif_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    resp = client.patch(f"/milestones/{mid}", json={"is_completed": True}, headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert resp.json()["is_completed"] is True


def test_delete_milestone_by_proposer(client, alif_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    resp = client.delete(f"/milestones/{mid}", headers=auth_header(alif_token))
    assert resp.status_code == 200


def test_cannot_delete_confirmed_milestone(client, alif_token, syifa_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    client.post(f"/milestones/{mid}/approve", headers=auth_header(alif_token))
    client.post(f"/milestones/{mid}/approve", headers=auth_header(syifa_token))
    resp = client.delete(f"/milestones/{mid}", headers=auth_header(alif_token))
    assert resp.status_code == 400
```

- [ ] **Step 2: Create routes/milestones.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Milestone, MilestoneApproval, User
from app.schemas import MilestoneCreate, MilestoneOut, MilestoneUpdate

router = APIRouter(prefix="/milestones", tags=["milestones"])


def milestone_to_out(milestone: Milestone, current_user_id: int, partner_id: int) -> MilestoneOut:
    approver_ids = {a.user_id for a in milestone.approvals}
    return MilestoneOut(
        id=milestone.id,
        title=milestone.title,
        description=milestone.description,
        target_date=milestone.target_date,
        proposed_by=milestone.proposed_by,
        proposer_name=milestone.proposer.display_name,
        is_confirmed=milestone.is_confirmed,
        is_completed=milestone.is_completed,
        is_approved_by_me=current_user_id in approver_ids,
        is_approved_by_partner=partner_id in approver_ids,
        created_at=milestone.created_at,
    )


@router.get("", response_model=list[MilestoneOut])
def list_milestones(
    current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)
):
    milestones = db.query(Milestone).order_by(Milestone.target_date.asc().nullslast(), Milestone.created_at.desc()).all()
    return [milestone_to_out(m, current_user.id, current_user.partner_id) for m in milestones]


@router.post("", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
def create_milestone(
    body: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    milestone = Milestone(
        title=body.title,
        description=body.description,
        target_date=body.target_date,
        proposed_by=current_user.id,
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone_to_out(milestone, current_user.id, current_user.partner_id)


@router.post("/{milestone_id}/approve", response_model=MilestoneOut)
def approve_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    existing = (
        db.query(MilestoneApproval)
        .filter(MilestoneApproval.milestone_id == milestone_id, MilestoneApproval.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already approved")

    approval = MilestoneApproval(milestone_id=milestone_id, user_id=current_user.id)
    db.add(approval)
    db.flush()

    approval_count = db.query(MilestoneApproval).filter(MilestoneApproval.milestone_id == milestone_id).count()
    if approval_count >= 2:
        milestone.is_confirmed = True

    db.commit()
    db.refresh(milestone)
    return milestone_to_out(milestone, current_user.id, current_user.partner_id)


@router.patch("/{milestone_id}", response_model=MilestoneOut)
def update_milestone(
    milestone_id: int,
    body: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    if body.title is not None:
        milestone.title = body.title
    if body.description is not None:
        milestone.description = body.description
    if body.target_date is not None:
        milestone.target_date = body.target_date
    if body.is_completed is not None:
        milestone.is_completed = body.is_completed

    db.commit()
    db.refresh(milestone)
    return milestone_to_out(milestone, current_user.id, current_user.partner_id)


@router.delete("/{milestone_id}")
def delete_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    if milestone.proposed_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the proposer can delete this milestone")
    if milestone.is_confirmed:
        raise HTTPException(status_code=400, detail="Cannot delete a confirmed milestone")

    db.delete(milestone)
    db.commit()
    return {"detail": "Milestone deleted"}
```

- [ ] **Step 3: Mount milestones router in main.py**

```python
from app.routes.milestones import router as milestones_router

app.include_router(milestones_router)
```

- [ ] **Step 4: Run milestones tests**

```bash
cd backend && source venv/bin/activate && pytest tests/test_milestones.py -v
```

Expected: All 6 tests pass.

- [ ] **Step 5: Run all backend tests**

```bash
cd backend && source venv/bin/activate && pytest -v
```

Expected: All tests pass (auth: 6, curfew: 4, rules: 6, questions: 5, milestones: 6 = 27 total).

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat(backend): milestones/roadmap with mutual approval"
```

---

## Task 7: Frontend Project Setup (Nuxt 4 + Tailwind)

**Files:**
- Create: `frontend/` via `npx nuxi@latest init`
- Create: `frontend/nuxt.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/assets/css/main.css`
- Create: `frontend/app.vue`

- [ ] **Step 1: Initialize Nuxt 4 project**

```bash
cd /home/seratusjuta/verses && npx nuxi@latest init frontend
cd frontend && npm install
```

- [ ] **Step 2: Install Tailwind CSS**

```bash
cd frontend && npm install -D @nuxtjs/tailwindcss
```

- [ ] **Step 3: Install Google Fonts**

```bash
cd frontend && npm install -D @nuxtjs/google-fonts
```

- [ ] **Step 4: Update nuxt.config.ts**

```typescript
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },
  modules: ['@nuxtjs/tailwindcss', '@nuxtjs/google-fonts'],

  googleFonts: {
    families: {
      'Playfair Display': [400, 600, 700],
      'Inter': [300, 400, 500, 600],
    },
  },

  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 5: Create tailwind.config.ts**

```typescript
import type { Config } from 'tailwindcss'

export default {
  content: [
    './components/**/*.{vue,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './app.vue',
  ],
  theme: {
    extend: {
      colors: {
        verse: {
          bg: '#F5F5F5',
          slate: '#6B7FA3',
          gold: '#C5A55A',
          text: '#2D3748',
          rose: '#B07D8E',
          'slate-light': '#E8ECF1',
          'gold-light': '#F5ECD7',
        },
      },
      fontFamily: {
        serif: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
} satisfies Config
```

- [ ] **Step 6: Create assets/css/main.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-verse-bg text-verse-text font-sans;
  }

  h1, h2, h3, h4 {
    @apply font-serif;
  }
}
```

- [ ] **Step 7: Create minimal app.vue**

```vue
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
```

- [ ] **Step 8: Verify dev server starts**

```bash
cd frontend && npx nuxt dev --port 3000
```

Expected: Dev server starts at http://localhost:3000 without errors.

- [ ] **Step 9: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): Nuxt 4 project setup with Tailwind CSS and design tokens"
```

---

## Task 8: Frontend Auth (useAuth + useApi + Middleware)

**Files:**
- Create: `frontend/composables/useAuth.ts`
- Create: `frontend/composables/useApi.ts`
- Create: `frontend/middleware/auth.global.ts`
- Create: `frontend/pages/login.vue`

- [ ] **Step 1: Create useAuth.ts**

```typescript
interface User {
  id: number
  username: string
  display_name: string
  partner: {
    id: number
    username: string
    display_name: string
    is_online: boolean
  } | null
}

interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export const useAuth = () => {
  const user = useState<User | null>('auth-user', () => null)
  const token = useCookie('verse-token')
  const refreshToken = useCookie('verse-refresh-token')
  const config = useRuntimeConfig()

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  async function login(username: string, password: string): Promise<void> {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    const data = await $fetch<LoginResponse>(`${config.public.apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    })

    token.value = data.access_token
    refreshToken.value = data.refresh_token
    await fetchUser()
  }

  async function fetchUser(): Promise<void> {
    if (!token.value) return
    try {
      const data = await $fetch<User>(`${config.public.apiBase}/auth/me`, {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      user.value = data
    } catch {
      token.value = null
      refreshToken.value = null
      user.value = null
    }
  }

  async function refresh(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const data = await $fetch<{ access_token: string }>(`${config.public.apiBase}/auth/refresh`, {
        method: 'POST',
        body: { refresh_token: refreshToken.value },
      })
      token.value = data.access_token
      await fetchUser()
      return true
    } catch {
      logout()
      return false
    }
  }

  function logout(): void {
    token.value = null
    refreshToken.value = null
    user.value = null
    navigateTo('/login')
  }

  return { user, token, isAuthenticated, login, logout, fetchUser, refresh }
}
```

- [ ] **Step 2: Create useApi.ts**

```typescript
export const useApi = () => {
  const { token, refresh, logout } = useAuth()
  const config = useRuntimeConfig()

  async function api<T>(path: string, options: RequestInit & { body?: any } = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    }

    if (token.value) {
      headers['Authorization'] = `Bearer ${token.value}`
    }

    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
      options.body = JSON.stringify(options.body)
    }

    try {
      return await $fetch<T>(`${config.public.apiBase}${path}`, {
        ...options,
        headers,
      })
    } catch (error: any) {
      if (error?.status === 401) {
        const refreshed = await refresh()
        if (refreshed) {
          headers['Authorization'] = `Bearer ${token.value}`
          return await $fetch<T>(`${config.public.apiBase}${path}`, {
            ...options,
            headers,
          })
        }
        logout()
      }
      throw error
    }
  }

  return { api }
}
```

- [ ] **Step 3: Create auth.global.ts middleware**

```typescript
export default defineNuxtRouteMiddleware((to) => {
  const { isAuthenticated } = useAuth()

  if (to.path === '/login') {
    if (isAuthenticated.value) {
      return navigateTo('/ledger')
    }
    return
  }

  if (!isAuthenticated.value) {
    return navigateTo('/login')
  }
})
```

- [ ] **Step 4: Create pages/login.vue**

```vue
<script setup lang="ts">
definePageMeta({ layout: false })

const { login, isAuthenticated } = useAuth()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(username.value, password.value)
    navigateTo('/ledger')
  } catch {
    error.value = 'Invalid username or password'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (isAuthenticated.value) navigateTo('/ledger')
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center relative overflow-hidden bg-verse-bg">
    <!-- Mountain background -->
    <div class="absolute inset-0 pointer-events-none">
      <svg class="absolute bottom-0 w-full" viewBox="0 0 1440 400" preserveAspectRatio="none">
        <path d="M0,400 L0,280 Q180,120 360,200 Q540,80 720,180 Q900,60 1080,160 Q1260,100 1440,220 L1440,400 Z" fill="#6B7FA3" opacity="0.15"/>
        <path d="M0,400 L0,320 Q200,180 400,260 Q600,140 800,240 Q1000,120 1200,200 Q1350,160 1440,260 L1440,400 Z" fill="#6B7FA3" opacity="0.08"/>
      </svg>
      <!-- Topographic lines -->
      <svg class="absolute top-0 left-0 w-full h-full opacity-[0.03]">
        <pattern id="topo" width="100" height="100" patternUnits="userSpaceOnUse">
          <circle cx="50" cy="50" r="40" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
          <circle cx="50" cy="50" r="30" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
          <circle cx="50" cy="50" r="20" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
        </pattern>
        <rect width="100%" height="100%" fill="url(#topo)"/>
      </svg>
    </div>

    <!-- Login card -->
    <div class="relative z-10 w-full max-w-sm mx-4">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-serif text-verse-text tracking-wide">Verse</h1>
        <p class="text-verse-slate text-sm mt-2 font-light">A shared space for your journey together</p>
      </div>

      <form @submit.prevent="handleLogin" class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-8 border border-verse-slate/10">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-verse-text mb-1">Username</label>
            <input
              v-model="username"
              type="text"
              required
              class="w-full px-4 py-2.5 rounded-lg border border-verse-slate/20 bg-white focus:outline-none focus:ring-2 focus:ring-verse-slate/40 transition"
              placeholder="Enter your name"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-verse-text mb-1">Password</label>
            <input
              v-model="password"
              type="password"
              required
              class="w-full px-4 py-2.5 rounded-lg border border-verse-slate/20 bg-white focus:outline-none focus:ring-2 focus:ring-verse-slate/40 transition"
              placeholder="Enter your password"
            />
          </div>
        </div>

        <p v-if="error" class="text-red-500 text-sm mt-3">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full mt-6 py-2.5 bg-verse-slate text-white rounded-lg font-medium hover:bg-verse-slate/90 transition disabled:opacity-50"
        >
          {{ loading ? 'Entering...' : 'Enter the Verse' }}
        </button>
      </form>

      <!-- Geometric pattern divider -->
      <div class="flex justify-center mt-6 gap-1.5">
        <span v-for="i in 5" :key="i" class="w-1.5 h-1.5 rounded-full bg-verse-slate/20" />
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): auth system with login page, JWT composable, and route guard"
```

---

## Task 9: Frontend Layout & Navigation

**Files:**
- Create: `frontend/layouts/default.vue`
- Create: `frontend/components/NavBar.vue`

- [ ] **Step 1: Create NavBar.vue**

```vue
<script setup lang="ts">
const { user, logout } = useAuth()
const route = useRoute()

const navItems = [
  { path: '/ledger', label: 'Ledger', icon: '&#9874;' },
  { path: '/inquiry', label: 'Inquiry', icon: '&#10067;' },
  { path: '/roadmap', label: 'Roadmap', icon: '&#9670;' },
]

const isActive = (path: string) => route.path === path

const userColor = computed(() =>
  user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose'
)
</script>

<template>
  <nav class="bg-white/90 backdrop-blur-sm border-b border-verse-slate/10">
    <div class="max-w-4xl mx-auto px-4 flex items-center justify-between h-14">
      <NuxtLink to="/ledger" class="font-serif text-xl text-verse-text tracking-wide">Verse</NuxtLink>

      <div class="flex items-center gap-1">
        <NuxtLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="px-3 py-1.5 rounded-lg text-sm transition"
          :class="isActive(item.path) ? 'bg-verse-slate text-white' : 'text-verse-text hover:bg-verse-slate/10'"
        >
          {{ item.label }}
        </NuxtLink>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <span class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-medium" :class="userColor">
            {{ user?.display_name?.[0] }}
          </span>
          <span class="text-sm text-verse-text hidden sm:inline">{{ user?.display_name }}</span>
        </div>
        <button @click="logout" class="text-xs text-verse-slate hover:text-verse-text transition">
          Logout
        </button>
      </div>
    </div>
  </nav>
</template>
```

- [ ] **Step 2: Create layouts/default.vue**

```vue
<template>
  <div class="min-h-screen bg-verse-bg">
    <NavBar />
    <main class="max-w-4xl mx-auto px-4 py-6">
      <slot />
    </main>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): default layout with nav bar"
```

---

## Task 10: Frontend Ledger Page

**Files:**
- Create: `frontend/components/RuleCard.vue`
- Create: `frontend/components/EmergencyOverrideModal.vue`
- Create: `frontend/pages/ledger.vue`

- [ ] **Step 1: Create EmergencyOverrideModal.vue**

```vue
<script setup lang="ts">
const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
    <div class="bg-white rounded-2xl shadow-xl p-6 max-w-sm mx-4 w-full">
      <h3 class="font-serif text-lg text-verse-text mb-2">Adab Curfew Active</h3>
      <p class="text-sm text-verse-text/70 mb-4">
        It's currently within the quiet hours (10 PM - 4 AM). This action requires an emergency override.
      </p>
      <p class="text-sm text-verse-text/70 mb-6">
        Do you wish to proceed?
      </p>
      <div class="flex gap-3">
        <button
          @click="emit('cancel')"
          class="flex-1 py-2 rounded-lg border border-verse-slate/20 text-verse-text text-sm hover:bg-verse-slate/5 transition"
        >
          Respect the Curfew
        </button>
        <button
          @click="emit('confirm')"
          class="flex-1 py-2 rounded-lg bg-verse-gold text-white text-sm hover:bg-verse-gold/90 transition"
        >
          Override
        </button>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Create RuleCard.vue**

```vue
<script setup lang="ts">
interface Rule {
  id: number
  title: string
  description: string
  proposed_by: number
  proposer_name: string
  is_sealed: boolean
  is_agreed_by_me: boolean
  is_agreed_by_partner: boolean
  created_at: string
}

const props = defineProps<{ rule: Rule }>()
const emit = defineEmits<{
  sign: [ruleId: number]
  delete: [ruleId: number]
}>()

const { user } = useAuth()
const isMyProposal = computed(() => props.rule.proposed_by === user.value?.id)
</script>

<template>
  <div
    class="rounded-xl border p-5 transition"
    :class="rule.is_sealed
      ? 'bg-verse-gold-light border-verse-gold/30'
      : 'bg-white border-verse-slate/10'"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-1">
          <h3 class="font-serif text-lg text-verse-text">{{ rule.title }}</h3>
          <span v-if="rule.is_sealed" class="text-xs px-2 py-0.5 rounded-full bg-verse-gold text-white font-medium">
            Sealed
          </span>
        </div>
        <p class="text-sm text-verse-text/70">{{ rule.description }}</p>
      </div>

      <button
        v-if="isMyProposal && !rule.is_sealed"
        @click="emit('delete', rule.id)"
        class="text-verse-text/30 hover:text-red-400 transition text-lg"
        title="Delete rule"
      >
        &times;
      </button>
    </div>

    <div class="mt-4 flex items-center justify-between">
      <div class="flex items-center gap-3 text-xs text-verse-text/50">
        <span>Proposed by {{ rule.proposer_name }}</span>
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full" :class="rule.is_agreed_by_me ? 'bg-green-400' : 'bg-verse-slate/20'" />
          Me
        </span>
        <span class="flex items-center gap-1">
          <span class="w-2 h-2 rounded-full" :class="rule.is_agreed_by_partner ? 'bg-green-400' : 'bg-verse-slate/20'" />
          Partner
        </span>
      </div>

      <button
        v-if="!rule.is_agreed_by_me && !rule.is_sealed"
        @click="emit('sign', rule.id)"
        class="px-4 py-1.5 text-sm rounded-lg bg-verse-slate text-white hover:bg-verse-slate/90 transition"
      >
        Sign
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Create pages/ledger.vue**

```vue
<script setup lang="ts">
interface Rule {
  id: number
  title: string
  description: string
  proposed_by: number
  proposer_name: string
  is_sealed: boolean
  is_agreed_by_me: boolean
  is_agreed_by_partner: boolean
  created_at: string
}

const { api } = useApi()
const rules = ref<Rule[]>([])
const filter = ref<'all' | 'pending' | 'sealed'>('all')
const showNewForm = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const showOverrideModal = ref(false)
const pendingAction = ref<(() => Promise<void>) | null>(null)

async function loadRules() {
  rules.value = await api<Rule[]>('/rules')
}

const filteredRules = computed(() => {
  switch (filter.value) {
    case 'pending':
      return rules.value.filter(r => !r.is_agreed_by_me && !r.is_sealed)
    case 'sealed':
      return rules.value.filter(r => r.is_sealed)
    default:
      return rules.value
  }
})

async function tryAction(action: () => Promise<void>) {
  try {
    await action()
  } catch (error: any) {
    if (error?.status === 403 && error?.data?.detail?.toLowerCase().includes('curfew')) {
      pendingAction.value = action
      showOverrideModal.value = true
      return
    }
    throw error
  }
}

async function createRule(emergencyOverride = false) {
  await tryAction(async () => {
    await api('/rules', {
      method: 'POST',
      body: { title: newTitle.value, description: newDesc.value, emergency_override: emergencyOverride },
    })
    newTitle.value = ''
    newDesc.value = ''
    showNewForm.value = false
    await loadRules()
  })
}

async function signRule(ruleId: number) {
  await api(`/rules/${ruleId}/sign`, { method: 'POST' })
  await loadRules()
}

async function deleteRule(ruleId: number) {
  await api(`/rules/${ruleId}`, { method: 'DELETE' })
  await loadRules()
}

async function handleOverrideConfirm() {
  showOverrideModal.value = false
  if (pendingAction.value) {
    // Retry with emergency override
    await createRule(true)
    pendingAction.value = null
  }
}

onMounted(loadRules)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Distancing Ledger</h1>
        <p class="text-sm text-verse-text/50 mt-1">Seal and sign your shared agreements</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition"
      >
        {{ showNewForm ? 'Cancel' : '+ New Rule' }}
      </button>
    </div>

    <!-- New rule form -->
    <form v-if="showNewForm" @submit.prevent="() => createRule()" class="bg-white rounded-xl border border-verse-slate/10 p-5 mb-6">
      <input
        v-model="newTitle"
        placeholder="Rule title"
        required
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30"
      />
      <textarea
        v-model="newDesc"
        placeholder="Describe the rule..."
        required
        rows="3"
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none"
      />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
        Propose Rule
      </button>
    </form>

    <!-- Filter tabs -->
    <div class="flex gap-1 mb-4 bg-white rounded-lg p-1 border border-verse-slate/10 w-fit">
      <button
        v-for="f in (['all', 'pending', 'sealed'] as const)"
        :key="f"
        @click="filter = f"
        class="px-3 py-1 text-sm rounded-md transition"
        :class="filter === f ? 'bg-verse-slate text-white' : 'text-verse-text/60 hover:bg-verse-slate/5'"
      >
        {{ f === 'pending' ? 'Pending My Signature' : f.charAt(0).toUpperCase() + f.slice(1) }}
      </button>
    </div>

    <!-- Rules list -->
    <div class="space-y-3">
      <RuleCard
        v-for="rule in filteredRules"
        :key="rule.id"
        :rule="rule"
        @sign="signRule"
        @delete="deleteRule"
      />
      <p v-if="filteredRules.length === 0" class="text-center text-verse-text/40 py-8">
        No rules yet. Propose one to get started.
      </p>
    </div>

    <EmergencyOverrideModal
      v-if="showOverrideModal"
      @confirm="handleOverrideConfirm"
      @cancel="showOverrideModal = false; pendingAction = null"
    />
  </div>
</template>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): ledger page with rule cards, signing, and curfew override"
```

---

## Task 11: Frontend Inquiry Hub Page

**Files:**
- Create: `frontend/components/QuestionCard.vue`
- Create: `frontend/components/MountainBackground.vue`
- Create: `frontend/pages/inquiry.vue`

- [ ] **Step 1: Create MountainBackground.vue**

```vue
<template>
  <div class="relative flex items-center justify-center py-8 rounded-xl bg-verse-slate/5 overflow-hidden">
    <svg class="absolute bottom-0 w-full opacity-20" viewBox="0 0 400 100" preserveAspectRatio="none">
      <path d="M0,100 L0,60 Q50,20 100,50 Q150,10 200,40 Q250,15 300,45 Q350,25 400,55 L400,100 Z" fill="#6B7FA3"/>
    </svg>
    <div class="relative z-10 text-center">
      <p class="text-verse-slate/40 text-sm font-serif italic">Answer first to reveal</p>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Create QuestionCard.vue**

```vue
<script setup lang="ts">
interface Answer {
  id: number
  user_id: number
  username: string
  text: string
  created_at: string
}

interface Question {
  id: number
  text: string
  asked_by: number
  asker_name: string
  my_answer: Answer | null
  partner_answer: Answer | null
  created_at: string
}

const props = defineProps<{ question: Question }>()
const emit = defineEmits<{ answer: [questionId: number, text: string] }>()

const { user } = useAuth()
const answerText = ref('')
const showAnswerForm = ref(false)

const partnerName = computed(() => user.value?.partner?.display_name ?? 'Partner')
const hasMyAnswer = computed(() => !!props.question.my_answer)
const hasPartnerAnswer = computed(() => !!props.question.partner_answer)
const bothAnswered = computed(() => hasMyAnswer.value && hasPartnerAnswer.value)

function submitAnswer() {
  if (!answerText.value.trim()) return
  emit('answer', props.question.id, answerText.value)
  answerText.value = ''
  showAnswerForm.value = false
}
</script>

<template>
  <div class="bg-white rounded-xl border border-verse-slate/10 p-5">
    <div class="flex items-start justify-between mb-3">
      <div>
        <h3 class="font-serif text-lg text-verse-text">{{ question.text }}</h3>
        <p class="text-xs text-verse-text/40 mt-1">Asked by {{ question.asker_name }}</p>
      </div>
      <span
        v-if="bothAnswered"
        class="text-xs px-2 py-0.5 rounded-full bg-verse-gold text-white font-medium"
      >
        Revealed
      </span>
    </div>

    <div class="space-y-3 mt-4">
      <!-- My answer -->
      <div v-if="hasMyAnswer" class="rounded-lg p-3 bg-verse-slate/5 border border-verse-slate/10">
        <p class="text-xs font-medium text-verse-slate mb-1">Your answer</p>
        <p class="text-sm text-verse-text">{{ question.my_answer!.text }}</p>
      </div>

      <!-- Partner answer - revealed or hidden -->
      <div v-if="bothAnswered" class="rounded-lg p-3 bg-verse-rose/5 border border-verse-rose/10">
        <p class="text-xs font-medium text-verse-rose mb-1">{{ partnerName }}'s answer</p>
        <p class="text-sm text-verse-text">{{ question.partner_answer!.text }}</p>
      </div>
      <MountainBackground v-else-if="!hasMyAnswer" />

      <!-- Answer button / form -->
      <div v-if="!hasMyAnswer">
        <button
          v-if="!showAnswerForm"
          @click="showAnswerForm = true"
          class="w-full py-2 text-sm rounded-lg border border-verse-slate/20 text-verse-slate hover:bg-verse-slate/5 transition"
        >
          Write your answer
        </button>
        <form v-else @submit.prevent="submitAnswer" class="space-y-2">
          <textarea
            v-model="answerText"
            rows="3"
            placeholder="Share your thoughts..."
            class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm"
          />
          <div class="flex gap-2">
            <button type="submit" class="px-4 py-1.5 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
              Submit
            </button>
            <button type="button" @click="showAnswerForm = false" class="px-4 py-1.5 text-sm text-verse-text/50 hover:text-verse-text transition">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Create pages/inquiry.vue**

```vue
<script setup lang="ts">
interface Answer {
  id: number
  user_id: number
  username: string
  text: string
  created_at: string
}

interface Question {
  id: number
  text: string
  asked_by: number
  asker_name: string
  my_answer: Answer | null
  partner_answer: Answer | null
  created_at: string
}

const { api } = useApi()
const questions = ref<Question[]>([])
const showNewForm = ref(false)
const newText = ref('')
const showOverrideModal = ref(false)
const pendingAction = ref<(() => Promise<void>) | null>(null)

async function loadQuestions() {
  questions.value = await api<Question[]>('/questions')
}

async function tryAction(action: () => Promise<void>) {
  try {
    await action()
  } catch (error: any) {
    if (error?.status === 403 && error?.data?.detail?.toLowerCase().includes('curfew')) {
      pendingAction.value = action
      showOverrideModal.value = true
      return
    }
    throw error
  }
}

async function createQuestion(emergencyOverride = false) {
  await tryAction(async () => {
    await api('/questions', {
      method: 'POST',
      body: { text: newText.value, emergency_override: emergencyOverride },
    })
    newText.value = ''
    showNewForm.value = false
    await loadQuestions()
  })
}

async function answerQuestion(questionId: number, text: string, emergencyOverride = false) {
  await tryAction(async () => {
    await api(`/questions/${questionId}/answer`, {
      method: 'POST',
      body: { text, emergency_override: emergencyOverride },
    })
    await loadQuestions()
  })
}

async function handleOverrideConfirm() {
  showOverrideModal.value = false
  if (pendingAction.value) {
    await pendingAction.value()
    pendingAction.value = null
  }
}

onMounted(loadQuestions)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Inquiry Hub</h1>
        <p class="text-sm text-verse-text/50 mt-1">Ask, reflect, then reveal together</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition"
      >
        {{ showNewForm ? 'Cancel' : '+ New Question' }}
      </button>
    </div>

    <form v-if="showNewForm" @submit.prevent="() => createQuestion()" class="bg-white rounded-xl border border-verse-slate/10 p-5 mb-6">
      <textarea
        v-model="newText"
        placeholder="What would you like to explore together?"
        required
        rows="3"
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none"
      />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
        Ask Question
      </button>
    </form>

    <div class="space-y-4">
      <QuestionCard
        v-for="q in questions"
        :key="q.id"
        :question="q"
        @answer="answerQuestion"
      />
      <p v-if="questions.length === 0" class="text-center text-verse-text/40 py-8">
        No questions yet. Start exploring together.
      </p>
    </div>

    <EmergencyOverrideModal
      v-if="showOverrideModal"
      @confirm="handleOverrideConfirm"
      @cancel="showOverrideModal = false; pendingAction = null"
    />
  </div>
</template>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): inquiry hub with double-blind answer reveal"
```

---

## Task 12: Frontend Roadmap Page

**Files:**
- Create: `frontend/components/MilestoneCard.vue`
- Create: `frontend/pages/roadmap.vue`

- [ ] **Step 1: Create MilestoneCard.vue**

```vue
<script setup lang="ts">
interface Milestone {
  id: number
  title: string
  description: string
  target_date: string | null
  proposed_by: number
  proposer_name: string
  is_confirmed: boolean
  is_completed: boolean
  is_approved_by_me: boolean
  is_approved_by_partner: boolean
  created_at: string
}

const props = defineProps<{ milestone: Milestone }>()
const emit = defineEmits<{
  approve: [milestoneId: number]
  complete: [milestoneId: number]
  delete: [milestoneId: number]
}>()

const { user } = useAuth()
const isMyProposal = computed(() => props.milestone.proposed_by === user.value?.id)

const statusLabel = computed(() => {
  if (props.milestone.is_completed) return 'Completed'
  if (props.milestone.is_confirmed) return 'Confirmed'
  return 'Proposed'
})

const statusColor = computed(() => {
  if (props.milestone.is_completed) return 'bg-green-500'
  if (props.milestone.is_confirmed) return 'bg-verse-gold'
  return 'bg-verse-slate/30'
})

function formatDate(d: string | null) {
  if (!d) return null
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <div class="flex gap-4">
    <!-- Timeline line + dot -->
    <div class="flex flex-col items-center">
      <div class="w-3 h-3 rounded-full mt-1.5" :class="statusColor" />
      <div class="w-0.5 flex-1 bg-verse-slate/10 mt-1" />
    </div>

    <!-- Card -->
    <div
      class="flex-1 rounded-xl border p-5 mb-4 transition"
      :class="milestone.is_confirmed ? 'bg-verse-gold-light border-verse-gold/30' : 'bg-white border-verse-slate/10'"
    >
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-1">
            <h3 class="font-serif text-lg text-verse-text">{{ milestone.title }}</h3>
            <span class="text-xs px-2 py-0.5 rounded-full text-white font-medium" :class="statusColor">
              {{ statusLabel }}
            </span>
          </div>
          <p class="text-sm text-verse-text/70">{{ milestone.description }}</p>
          <p v-if="milestone.target_date" class="text-xs text-verse-text/40 mt-2">
            Target: {{ formatDate(milestone.target_date) }}
          </p>
        </div>

        <button
          v-if="isMyProposal && !milestone.is_confirmed"
          @click="emit('delete', milestone.id)"
          class="text-verse-text/30 hover:text-red-400 transition text-lg"
          title="Delete milestone"
        >
          &times;
        </button>
      </div>

      <div class="mt-4 flex items-center justify-between">
        <div class="flex items-center gap-3 text-xs text-verse-text/50">
          <span>By {{ milestone.proposer_name }}</span>
          <span class="flex items-center gap-1">
            <span class="w-2 h-2 rounded-full" :class="milestone.is_approved_by_me ? 'bg-green-400' : 'bg-verse-slate/20'" />
            Me
          </span>
          <span class="flex items-center gap-1">
            <span class="w-2 h-2 rounded-full" :class="milestone.is_approved_by_partner ? 'bg-green-400' : 'bg-verse-slate/20'" />
            Partner
          </span>
        </div>

        <div class="flex gap-2">
          <button
            v-if="!milestone.is_approved_by_me && !milestone.is_completed"
            @click="emit('approve', milestone.id)"
            class="px-3 py-1.5 text-sm rounded-lg bg-verse-slate text-white hover:bg-verse-slate/90 transition"
          >
            Approve
          </button>
          <button
            v-if="milestone.is_confirmed && !milestone.is_completed"
            @click="emit('complete', milestone.id)"
            class="px-3 py-1.5 text-sm rounded-lg bg-green-500 text-white hover:bg-green-600 transition"
          >
            Complete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Create pages/roadmap.vue**

```vue
<script setup lang="ts">
interface Milestone {
  id: number
  title: string
  description: string
  target_date: string | null
  proposed_by: number
  proposer_name: string
  is_confirmed: boolean
  is_completed: boolean
  is_approved_by_me: boolean
  is_approved_by_partner: boolean
  created_at: string
}

const { api } = useApi()
const milestones = ref<Milestone[]>([])
const showNewForm = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const newDate = ref('')

async function loadMilestones() {
  milestones.value = await api<Milestone[]>('/milestones')
}

async function createMilestone() {
  await api('/milestones', {
    method: 'POST',
    body: {
      title: newTitle.value,
      description: newDesc.value,
      target_date: newDate.value || null,
    },
  })
  newTitle.value = ''
  newDesc.value = ''
  newDate.value = ''
  showNewForm.value = false
  await loadMilestones()
}

async function approveMilestone(id: number) {
  await api(`/milestones/${id}/approve`, { method: 'POST' })
  await loadMilestones()
}

async function completeMilestone(id: number) {
  await api(`/milestones/${id}`, { method: 'PATCH', body: { is_completed: true } })
  await loadMilestones()
}

async function deleteMilestone(id: number) {
  await api(`/milestones/${id}`, { method: 'DELETE' })
  await loadMilestones()
}

onMounted(loadMilestones)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Marriage Roadmap</h1>
        <p class="text-sm text-verse-text/50 mt-1">Your journey together, one milestone at a time</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition"
      >
        {{ showNewForm ? 'Cancel' : '+ Propose Milestone' }}
      </button>
    </div>

    <form v-if="showNewForm" @submit.prevent="createMilestone" class="bg-white rounded-xl border border-verse-slate/10 p-5 mb-6">
      <input
        v-model="newTitle"
        placeholder="Milestone title"
        required
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30"
      />
      <textarea
        v-model="newDesc"
        placeholder="Describe this milestone..."
        required
        rows="3"
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none"
      />
      <input
        v-model="newDate"
        type="date"
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30"
      />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
        Propose
      </button>
    </form>

    <div>
      <MilestoneCard
        v-for="m in milestones"
        :key="m.id"
        :milestone="m"
        @approve="approveMilestone"
        @complete="completeMilestone"
        @delete="deleteMilestone"
      />
      <p v-if="milestones.length === 0" class="text-center text-verse-text/40 py-8">
        No milestones yet. Propose your first step forward.
      </p>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): roadmap page with milestone timeline and mutual approval"
```

---

## Task 13: Frontend Auth Init & Index Redirect

**Files:**
- Create: `frontend/plugins/auth.ts`
- Create: `frontend/pages/index.vue`

- [ ] **Step 1: Create plugins/auth.ts**

```typescript
export default defineNuxtPlugin(async () => {
  const { fetchUser, token } = useAuth()
  if (token.value) {
    await fetchUser()
  }
})
```

- [ ] **Step 2: Create pages/index.vue**

```vue
<script setup lang="ts">
definePageMeta({ layout: false })

onMounted(() => {
  navigateTo('/ledger')
})
</script>

<template>
  <div />
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): auth plugin and index redirect"
```

---

## Task 14: Integration Testing & Final Verification

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && source venv/bin/activate && pytest -v
```

Expected: All 27 tests pass.

- [ ] **Step 2: Start backend server**

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 3: Start frontend dev server**

```bash
cd frontend && npm run dev
```

- [ ] **Step 4: Manual smoke test**

1. Open http://localhost:3000 — should redirect to /login
2. Login as `alif` / `verse2024` — should redirect to /ledger
3. Create a rule, sign it
4. Navigate to Inquiry, create a question, answer it
5. Navigate to Roadmap, propose a milestone, approve it
6. Logout, login as `syifa`, verify partner interactions

- [ ] **Step 5: Commit any fixes**

```bash
git add -A && git commit -m "fix: integration testing fixes"
```
