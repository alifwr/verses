# Supabase Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace SQLite + custom JWT auth with Supabase PostgreSQL + Supabase Auth (Google OAuth), with invite-based partner pairing.

**Architecture:** Frontend uses `@supabase/supabase-js` for Google OAuth sign-in. Backend validates Supabase JWTs and keeps SQLAlchemy ORM pointing at Supabase PostgreSQL. Users are auto-created in the app's `users` table on first valid token. Partner pairing uses invite codes.

**Tech Stack:** Supabase (Auth + PostgreSQL), `@supabase/supabase-js`, `PyJWT`, `psycopg2-binary`, SQLAlchemy (PostgreSQL dialect), FastAPI

---

## File Structure

### Backend files to create
- `backend/app/supabase_auth.py` — Supabase JWT validation + user sync logic

### Backend files to modify
- `backend/app/config.py` — Add Supabase env vars, remove old JWT settings
- `backend/app/database.py` — Remove SQLite `check_same_thread`, support PostgreSQL
- `backend/app/models.py` — User: add `supabase_uid`/`email`/`avatar_url`, drop `hashed_password`. Remove `Session` model. Add `InviteCode` model.
- `backend/app/schemas.py` — Add invite schemas, update `UserOut`
- `backend/app/routes/auth.py` — Replace login/refresh with invite endpoints, keep `/me`
- `backend/app/main.py` — Remove seed import/call
- `backend/requirements.txt` — Swap deps
- `backend/Dockerfile` — No changes needed
- `backend/tests/conftest.py` — Replace password-based auth with JWT mocking
- `backend/tests/test_auth.py` — Rewrite for new auth flow
- `backend/tests/test_rules.py` — Update to use new fixtures
- `backend/tests/test_questions.py` — Update to use new fixtures
- `backend/tests/test_milestones.py` — Update to use new fixtures
- `backend/tests/test_talks.py` — Update to use new fixtures
- `backend/tests/test_activity.py` — Update to use new fixtures

### Backend files to delete
- `backend/app/auth.py` — Replaced by `supabase_auth.py`
- `backend/app/seed.py` — No longer needed

### Frontend files to create
- `frontend/app/utils/supabase.ts` — Supabase client singleton
- `frontend/app/pages/invite.vue` — Invite code entry page for new unpaired users
- `frontend/app/pages/auth/callback.vue` — OAuth callback handler

### Frontend files to modify
- `frontend/nuxt.config.ts` — Add Supabase env vars to runtimeConfig
- `frontend/package.json` — Add `@supabase/supabase-js`
- `frontend/app/composables/useAuth.ts` — Rewrite to use Supabase auth
- `frontend/app/composables/useApi.ts` — Get token from Supabase session
- `frontend/app/plugins/auth.ts` — Use Supabase session restore
- `frontend/app/middleware/auth.global.ts` — Check Supabase session
- `frontend/app/pages/login.vue` — Replace form with Google sign-in button

### Config files to modify
- `docker-compose.yml` — Add Supabase env vars, remove `db-data` volume

---

## Task 1: Backend — Config and Database Layer

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/database.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Update requirements.txt**

Replace the contents of `backend/requirements.txt`:

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
PyJWT[crypto]==2.9.0
python-multipart==0.0.9
pytest==8.3.0
httpx==0.27.0
pydantic-settings==2.5.2
```

Removed: `python-jose[cryptography]`, `passlib[bcrypt]`, `bcrypt`
Added: `psycopg2-binary`, `PyJWT[crypto]`

- [ ] **Step 2: Update config.py**

Replace `backend/app/config.py` with:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS


settings = Settings()
```

- [ ] **Step 3: Update database.py**

Replace `backend/app/database.py` with:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

engine = create_engine(settings.DATABASE_URL)
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

Only change: removed `connect_args={"check_same_thread": False}` (SQLite-specific).

- [ ] **Step 4: Install dependencies locally and verify import**

```bash
cd backend && pip install -r requirements.txt
python -c "import psycopg2; import jwt; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/config.py backend/app/database.py
git commit -m "feat: update config and database layer for Supabase PostgreSQL"
```

---

## Task 2: Backend — Update Models

**Files:**
- Modify: `backend/app/models.py`

- [ ] **Step 1: Replace models.py**

Replace `backend/app/models.py` with:

```python
from datetime import datetime, date, timezone, timedelta
from typing import Optional, List
import secrets

from sqlalchemy import String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

GMT7 = timezone(timedelta(hours=7))


def now_gmt7() -> datetime:
    return datetime.now(GMT7)


def generate_invite_code() -> str:
    return secrets.token_urlsafe(8)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    supabase_uid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    partner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)

    partner: Mapped[Optional["User"]] = relationship("User", remote_side="User.id", foreign_keys=[partner_id])


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, default=generate_invite_code)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    used_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    acceptor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[used_by])


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_sealed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)

    proposer: Mapped["User"] = relationship("User", foreign_keys=[proposed_by])
    signatures: Mapped[List["RuleSignature"]] = relationship("RuleSignature", back_populates="rule", cascade="all, delete-orphan")


class RuleSignature(Base):
    __tablename__ = "rule_signatures"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    signed_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)

    rule: Mapped["Rule"] = relationship("Rule", back_populates="signatures")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    asked_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)

    asker: Mapped["User"] = relationship("User", foreign_keys=[asked_by])
    answers: Mapped[List["Answer"]] = relationship("Answer", back_populates="question")


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)

    question: Mapped["Question"] = relationship("Question", back_populates="answers")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    proposed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)

    proposer: Mapped["User"] = relationship("User", foreign_keys=[proposed_by])
    approvals: Mapped[List["MilestoneApproval"]] = relationship("MilestoneApproval", back_populates="milestone", cascade="all, delete-orphan")


class MilestoneApproval(Base):
    __tablename__ = "milestone_approvals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    milestone_id: Mapped[int] = mapped_column(ForeignKey("milestones.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)

    milestone: Mapped["Milestone"] = relationship("Milestone", back_populates="approvals")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class Talk(Base):
    __tablename__ = "talks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    queued_for: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)

    proposer: Mapped["User"] = relationship("User", foreign_keys=[proposed_by])
    notes: Mapped[List["TalkNote"]] = relationship("TalkNote", back_populates="talk", cascade="all, delete-orphan")


class TalkNote(Base):
    __tablename__ = "talk_notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    talk_id: Mapped[int] = mapped_column(ForeignKey("talks.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)

    talk: Mapped["Talk"] = relationship("Talk", back_populates="notes")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
```

Changes from original:
- `User`: removed `hashed_password`, `username`, `sessions` relationship. Added `supabase_uid`, `email`, `avatar_url`.
- Removed `Session` model entirely.
- Added `InviteCode` model with `code`, `created_by`, `used_by`, `expires_at`.

- [ ] **Step 2: Commit**

```bash
git add backend/app/models.py
git commit -m "feat: update User model for Supabase auth, add InviteCode model"
```

---

## Task 3: Backend — Supabase Auth Module

**Files:**
- Create: `backend/app/supabase_auth.py`
- Modify: `backend/app/schemas.py`
- Delete: `backend/app/auth.py`
- Delete: `backend/app/seed.py`

- [ ] **Step 1: Create supabase_auth.py**

Create `backend/app/supabase_auth.py`:

```python
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

security = HTTPBearer()


def decode_supabase_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_supabase_jwt(credentials.credentials)
    supabase_uid = payload.get("sub")
    if not supabase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
    if user is None:
        # Auto-create user on first login
        email = payload.get("email", "")
        user_metadata = payload.get("user_metadata", {})
        display_name = user_metadata.get("full_name") or user_metadata.get("name") or email.split("@")[0]
        avatar_url = user_metadata.get("avatar_url") or user_metadata.get("picture")

        user = User(
            supabase_uid=supabase_uid,
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
```

- [ ] **Step 2: Update schemas.py**

Replace `backend/app/schemas.py` with:

```python
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


# --- Auth schemas ---

class PartnerInfo(BaseModel):
    id: int
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    is_online: bool

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    has_partner: bool
    partner: Optional[PartnerInfo] = None

    model_config = {"from_attributes": True}


class InviteCodeCreate(BaseModel):
    pass


class InviteCodeOut(BaseModel):
    code: str
    created_at: datetime
    expires_at: datetime
    is_used: bool

    model_config = {"from_attributes": True}


class InviteAccept(BaseModel):
    code: str


# --- Rules schemas ---

class RuleCreate(BaseModel):
    title: str
    description: Optional[str] = None


class RuleOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    proposed_by: int
    proposer_name: str
    is_sealed: bool
    is_agreed_by_me: bool
    is_agreed_by_partner: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Questions schemas ---

class QuestionCreate(BaseModel):
    text: str


class AnswerCreate(BaseModel):
    text: str


class AnswerOut(BaseModel):
    id: int
    user_id: int
    display_name: str
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: int
    text: str
    asked_by: int
    asker_name: str
    my_answer: Optional[AnswerOut] = None
    partner_answer: Optional[AnswerOut] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Milestones schemas ---

class MilestoneCreate(BaseModel):
    title: str
    description: Optional[str] = None
    target_date: Optional[date] = None


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[date] = None
    is_completed: Optional[bool] = None


class MilestoneOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    target_date: Optional[date] = None
    proposed_by: int
    proposer_name: str
    is_confirmed: bool
    is_completed: bool
    is_approved_by_me: bool
    is_approved_by_partner: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Talks schemas ---

class TalkCreate(BaseModel):
    title: str
    description: Optional[str] = None
    queued_for: Optional[datetime] = None


class TalkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    queued_for: Optional[datetime] = None


class TalkNoteCreate(BaseModel):
    text: str


class TalkNoteOut(BaseModel):
    id: int
    user_id: int
    display_name: str
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TalkOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    proposed_by: int
    proposer_name: str
    status: str
    queued_for: Optional[datetime] = None
    notes: list[TalkNoteOut] = []
    note_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


# Activity
class ActivityOut(BaseModel):
    type: str
    actor: str
    summary: str
    timestamp: datetime
```

Changes: Removed `Token`, `TokenRefresh`, `TokenOut`. Added `InviteCodeCreate`, `InviteCodeOut`, `InviteAccept`. Updated `UserOut` to use `email` instead of `username`, added `has_partner`, `avatar_url`. Updated `PartnerInfo` similarly. Changed `AnswerOut.username` and `TalkNoteOut.username` to `display_name`.

- [ ] **Step 3: Delete old auth files**

```bash
rm backend/app/auth.py backend/app/seed.py
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/supabase_auth.py backend/app/schemas.py
git add -u backend/app/auth.py backend/app/seed.py
git commit -m "feat: add Supabase JWT auth module, update schemas, remove old auth"
```

---

## Task 4: Backend — Auth Routes (Invite Flow)

**Files:**
- Modify: `backend/app/routes/auth.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Replace routes/auth.py**

Replace `backend/app/routes/auth.py` with:

```python
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.supabase_auth import get_current_user
from app.database import get_db
from app.models import InviteCode, User, now_gmt7
from app.schemas import InviteAccept, InviteCodeOut, UserOut, PartnerInfo

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    partner = None
    if current_user.partner:
        partner = PartnerInfo(
            id=current_user.partner.id,
            email=current_user.partner.email,
            display_name=current_user.partner.display_name,
            avatar_url=current_user.partner.avatar_url,
            is_online=current_user.partner.is_online,
        )
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        has_partner=current_user.partner_id is not None,
        partner=partner,
    )


@router.post("/invite", response_model=InviteCodeOut, status_code=status.HTTP_201_CREATED)
def create_invite(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.partner_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a partner",
        )

    # Expire any existing unused invites from this user
    existing = (
        db.query(InviteCode)
        .filter(InviteCode.created_by == current_user.id, InviteCode.used_by.is_(None))
        .all()
    )
    for inv in existing:
        db.delete(inv)

    invite = InviteCode(
        created_by=current_user.id,
        expires_at=now_gmt7() + timedelta(days=7),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return InviteCodeOut(
        code=invite.code,
        created_at=invite.created_at,
        expires_at=invite.expires_at,
        is_used=False,
    )


@router.post("/accept-invite", response_model=UserOut)
def accept_invite(
    body: InviteAccept,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.partner_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a partner",
        )

    invite = (
        db.query(InviteCode)
        .filter(InviteCode.code == body.code, InviteCode.used_by.is_(None))
        .first()
    )
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invite code",
        )

    if invite.expires_at < now_gmt7():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite code has expired",
        )

    if invite.created_by == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot accept your own invite",
        )

    # Pair the users
    inviter = db.query(User).filter(User.id == invite.created_by).first()
    current_user.partner_id = inviter.id
    inviter.partner_id = current_user.id
    invite.used_by = current_user.id
    db.commit()
    db.refresh(current_user)

    partner = PartnerInfo(
        id=inviter.id,
        email=inviter.email,
        display_name=inviter.display_name,
        avatar_url=inviter.avatar_url,
        is_online=inviter.is_online,
    )
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        has_partner=True,
        partner=partner,
    )
```

- [ ] **Step 2: Update main.py**

Replace `backend/app/main.py` with:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routes.auth import router as auth_router
from app.routes.rules import router as rules_router
from app.routes.questions import router as questions_router
from app.routes.milestones import router as milestones_router
from app.routes.activity import router as activity_router
from app.routes.talks import router as talks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(rules_router)
app.include_router(questions_router)
app.include_router(milestones_router)
app.include_router(activity_router)
app.include_router(talks_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

Changes: removed `SessionLocal` import, removed `seed_users` import and call.

- [ ] **Step 3: Commit**

```bash
git add backend/app/routes/auth.py backend/app/main.py
git commit -m "feat: replace login/refresh with invite-based pairing endpoints"
```

---

## Task 5: Backend — Update All Route Imports

**Files:**
- Modify: `backend/app/routes/rules.py`
- Modify: `backend/app/routes/questions.py`
- Modify: `backend/app/routes/milestones.py`
- Modify: `backend/app/routes/talks.py`
- Modify: `backend/app/routes/activity.py`

Every route file currently imports `from app.auth import get_current_user`. This must change to `from app.supabase_auth import get_current_user`.

- [ ] **Step 1: Update imports in all route files**

In each of these files, replace the import line:

`backend/app/routes/rules.py` line 3:
```python
# old
from app.auth import get_current_user
# new
from app.supabase_auth import get_current_user
```

`backend/app/routes/questions.py` line 3:
```python
# old
from app.auth import get_current_user
# new
from app.supabase_auth import get_current_user
```

`backend/app/routes/milestones.py` line 3:
```python
# old
from app.auth import get_current_user
# new
from app.supabase_auth import get_current_user
```

`backend/app/routes/talks.py` line 3:
```python
# old
from app.auth import get_current_user
# new
from app.supabase_auth import get_current_user
```

`backend/app/routes/activity.py` line 4:
```python
# old
from app.auth import get_current_user
# new
from app.supabase_auth import get_current_user
```

- [ ] **Step 2: Update AnswerOut construction in questions.py**

In `backend/app/routes/questions.py`, the `answer_to_out` function uses `answer.user.username`. Update to use `display_name`:

```python
def answer_to_out(answer: Answer) -> AnswerOut:
    return AnswerOut(
        id=answer.id,
        user_id=answer.user_id,
        display_name=answer.user.display_name,
        text=answer.text,
        created_at=answer.created_at,
    )
```

- [ ] **Step 3: Update TalkNoteOut construction in talks.py**

In `backend/app/routes/talks.py`, the `note_to_out` function uses `note.user.display_name` already but the field was `username`. It now maps to `display_name` in the schema:

```python
def note_to_out(note: TalkNote) -> TalkNoteOut:
    return TalkNoteOut(
        id=note.id,
        user_id=note.user_id,
        display_name=note.user.display_name,
        text=note.text,
        created_at=note.created_at,
    )
```

- [ ] **Step 4: Verify all imports resolve**

```bash
cd backend && python -c "from app.routes import auth, rules, questions, milestones, talks, activity; print('OK')"
```

Expected: `OK` (may warn about missing DB connection, but imports should resolve)

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/
git commit -m "feat: update all routes to use Supabase auth import"
```

---

## Task 6: Backend — Update Tests

**Files:**
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/test_auth.py`
- Modify: `backend/tests/test_rules.py`
- Modify: `backend/tests/test_questions.py`
- Modify: `backend/tests/test_milestones.py`
- Modify: `backend/tests/test_talks.py`
- Modify: `backend/tests/test_activity.py`

Since we no longer have password-based login, tests need to mock Supabase JWT validation. We'll create test users directly in the DB and mock `get_current_user`.

- [ ] **Step 1: Replace conftest.py**

Replace `backend/tests/conftest.py` with:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.supabase_auth import get_current_user

TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


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
    alif, syifa = create_test_users(db_session)

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
def alif_client(client, db, alif_user):
    """Client that is authenticated as alif."""
    app.dependency_overrides[get_current_user] = lambda: alif_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def syifa_client(client, db, syifa_user):
    """Client that is authenticated as syifa."""
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)
```

Key change: Instead of getting tokens via login, we override `get_current_user` dependency directly. Each test gets `alif_client` or `syifa_client` fixtures that are already authenticated.

- [ ] **Step 2: Replace test_auth.py**

Replace `backend/tests/test_auth.py` with:

```python
from app.models import InviteCode, User


def test_me_authenticated(alif_client):
    resp = alif_client.get("/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "alif@test.com"
    assert data["display_name"] == "Alif"
    assert data["has_partner"] is True
    assert data["partner"]["display_name"] == "Syifa"


def test_me_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 403  # HTTPBearer returns 403 when no token


def test_create_invite(db, alif_user):
    # Unpair alif first so they can create an invite
    syifa = db.query(User).filter(User.email == "syifa@test.com").first()
    alif_user.partner_id = None
    syifa.partner_id = None
    db.commit()

    from fastapi.testclient import TestClient
    from app.main import app
    from app.supabase_auth import get_current_user
    from app.database import get_db

    app.dependency_overrides[get_current_user] = lambda: alif_user
    app.dependency_overrides[get_db] = lambda: (yield db) if False else None

    # Need to use the existing db override
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        resp = c.post("/auth/invite")
        assert resp.status_code == 201
        data = resp.json()
        assert "code" in data
        assert data["is_used"] is False

    app.dependency_overrides.pop(get_current_user, None)


def test_create_invite_already_paired(alif_client):
    resp = alif_client.post("/auth/invite")
    assert resp.status_code == 400
    assert "already have a partner" in resp.json()["detail"]


def test_accept_invite(db):
    # Create two unpaired users
    user_a = User(supabase_uid="test-uid-a", email="a@test.com", display_name="A")
    user_b = User(supabase_uid="test-uid-b", email="b@test.com", display_name="B")
    db.add(user_a)
    db.add(user_b)
    db.commit()
    db.refresh(user_a)
    db.refresh(user_b)

    from fastapi.testclient import TestClient
    from app.main import app
    from app.supabase_auth import get_current_user
    from app.database import get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # User A creates invite
    app.dependency_overrides[get_current_user] = lambda: user_a
    with TestClient(app) as c:
        resp = c.post("/auth/invite")
        assert resp.status_code == 201
        code = resp.json()["code"]

    # User B accepts invite
    app.dependency_overrides[get_current_user] = lambda: user_b
    with TestClient(app) as c:
        resp = c.post("/auth/accept-invite", json={"code": code})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_partner"] is True
        assert data["partner"]["display_name"] == "A"

    # Verify both are paired
    db.refresh(user_a)
    db.refresh(user_b)
    assert user_a.partner_id == user_b.id
    assert user_b.partner_id == user_a.id

    app.dependency_overrides.pop(get_current_user, None)


def test_accept_own_invite(db):
    user_a = User(supabase_uid="test-uid-own", email="own@test.com", display_name="Own")
    db.add(user_a)
    db.commit()
    db.refresh(user_a)

    from fastapi.testclient import TestClient
    from app.main import app
    from app.supabase_auth import get_current_user
    from app.database import get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user_a

    with TestClient(app) as c:
        resp = c.post("/auth/invite")
        code = resp.json()["code"]
        resp = c.post("/auth/accept-invite", json={"code": code})
        assert resp.status_code == 400
        assert "own invite" in resp.json()["detail"]

    app.dependency_overrides.pop(get_current_user, None)
```

- [ ] **Step 3: Update test_rules.py**

In `backend/tests/test_rules.py`, replace all uses of `alif_token`/`syifa_token` and `auth_header(...)` with the new `alif_client`/`syifa_client` fixtures. Replace every:
- `client.get("/rules", headers=auth_header(alif_token))` with `alif_client.get("/rules")`
- `client.post("/rules", ..., headers=auth_header(alif_token))` with `alif_client.post("/rules", ...)`
- Same pattern for `syifa_token` -> `syifa_client`

Remove the import of `auth_header` from `tests.conftest`.

- [ ] **Step 4: Update test_questions.py**

Same pattern as Step 3: replace `client` + `auth_header(token)` with `alif_client`/`syifa_client`.

- [ ] **Step 5: Update test_milestones.py**

Same pattern as Step 3.

- [ ] **Step 6: Update test_talks.py**

Same pattern as Step 3.

- [ ] **Step 7: Update test_activity.py**

Same pattern as Step 3.

- [ ] **Step 8: Run all tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 9: Commit**

```bash
git add backend/tests/
git commit -m "feat: update all tests for Supabase auth (mock get_current_user)"
```

---

## Task 7: Frontend — Supabase Client and Auth Composable

**Files:**
- Create: `frontend/app/utils/supabase.ts`
- Modify: `frontend/nuxt.config.ts`
- Modify: `frontend/package.json` (install dep)
- Modify: `frontend/app/composables/useAuth.ts`
- Modify: `frontend/app/composables/useApi.ts`

- [ ] **Step 1: Install @supabase/supabase-js**

```bash
cd frontend && npm install @supabase/supabase-js
```

- [ ] **Step 2: Update nuxt.config.ts**

Replace `frontend/nuxt.config.ts` with:

```typescript
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },
  modules: ['@nuxtjs/tailwindcss', '@nuxtjs/google-fonts'],

  css: ['~/assets/css/main.css'],

  tailwindcss: {
    cssPath: '~/assets/css/main.css',
  },

  googleFonts: {
    families: {
      'Playfair Display': [400, 600, 700],
      'Inter': [300, 400, 500, 600],
    },
  },

  runtimeConfig: {
    public: {
      apiBase: 'https://verse-api.alifpunya.com',
      supabaseUrl: '',
      supabaseAnonKey: '',
    },
  },
})
```

- [ ] **Step 3: Create supabase.ts client**

Create `frontend/app/utils/supabase.ts`:

```typescript
import { createClient, type SupabaseClient } from '@supabase/supabase-js'

let client: SupabaseClient | null = null

export function useSupabaseClient(): SupabaseClient {
  if (client) return client

  const config = useRuntimeConfig()
  client = createClient(config.public.supabaseUrl, config.public.supabaseAnonKey)
  return client
}
```

- [ ] **Step 4: Replace useAuth.ts**

Replace `frontend/app/composables/useAuth.ts` with:

```typescript
import { useSupabaseClient } from '~/utils/supabase'

interface Partner {
  id: number
  email: string
  display_name: string
  avatar_url: string | null
  is_online: boolean
}

interface User {
  id: number
  email: string
  display_name: string
  avatar_url: string | null
  has_partner: boolean
  partner: Partner | null
}

export const useAuth = () => {
  const user = useState<User | null>('auth-user', () => null)
  const config = useRuntimeConfig()

  const isAuthenticated = computed(() => !!user.value)
  const hasPartner = computed(() => !!user.value?.has_partner)

  async function getAccessToken(): Promise<string | null> {
    const supabase = useSupabaseClient()
    const { data } = await supabase.auth.getSession()
    return data.session?.access_token ?? null
  }

  async function signInWithGoogle(): Promise<void> {
    const supabase = useSupabaseClient()
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
  }

  async function fetchUser(): Promise<void> {
    const token = await getAccessToken()
    if (!token) return

    try {
      const data = await $fetch<User>(`${config.public.apiBase}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      user.value = data
    } catch {
      user.value = null
    }
  }

  async function logout(): Promise<void> {
    const supabase = useSupabaseClient()
    await supabase.auth.signOut()
    user.value = null
    navigateTo('/login')
  }

  return { user, isAuthenticated, hasPartner, getAccessToken, signInWithGoogle, fetchUser, logout }
}
```

- [ ] **Step 5: Replace useApi.ts**

Replace `frontend/app/composables/useApi.ts` with:

```typescript
export const useApi = () => {
  const { getAccessToken, logout } = useAuth()
  const config = useRuntimeConfig()

  async function api<T>(path: string, options: any = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...(options.headers || {}),
    }

    const token = await getAccessToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
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
      if (error?.status === 401 || error?.statusCode === 401) {
        await logout()
      }
      throw error
    }
  }

  return { api }
}
```

Simplified: no refresh logic needed (Supabase handles token refresh internally).

- [ ] **Step 6: Commit**

```bash
cd frontend && git add app/utils/supabase.ts app/composables/useAuth.ts app/composables/useApi.ts nuxt.config.ts package.json package-lock.json
git commit -m "feat: add Supabase client, rewrite auth composables for Google OAuth"
```

---

## Task 8: Frontend — Auth Pages and Middleware

**Files:**
- Modify: `frontend/app/pages/login.vue`
- Create: `frontend/app/pages/auth/callback.vue`
- Create: `frontend/app/pages/invite.vue`
- Modify: `frontend/app/plugins/auth.ts`
- Modify: `frontend/app/middleware/auth.global.ts`

- [ ] **Step 1: Replace login.vue**

Replace `frontend/app/pages/login.vue` with:

```vue
<script setup lang="ts">
definePageMeta({ layout: false })

const { signInWithGoogle, isAuthenticated } = useAuth()
const loading = ref(false)
const error = ref('')

async function handleGoogleLogin() {
  loading.value = true
  error.value = ''
  try {
    await signInWithGoogle()
  } catch {
    error.value = 'Failed to sign in. Please try again.'
    loading.value = false
  }
}

onMounted(() => {
  if (isAuthenticated.value) navigateTo('/rules')
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center relative overflow-hidden bg-verse-bg">
    <!-- Mountain background SVG -->
    <div class="absolute inset-0 pointer-events-none">
      <svg class="absolute bottom-0 w-full" viewBox="0 0 1440 400" preserveAspectRatio="none">
        <path d="M0,400 L0,280 Q180,120 360,200 Q540,80 720,180 Q900,60 1080,160 Q1260,100 1440,220 L1440,400 Z" fill="#6B7FA3" opacity="0.15"/>
        <path d="M0,400 L0,320 Q200,180 400,260 Q600,140 800,240 Q1000,120 1200,200 Q1350,160 1440,260 L1440,400 Z" fill="#6B7FA3" opacity="0.08"/>
      </svg>
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

      <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-8 border border-verse-slate/10">
        <p v-if="error" class="text-red-500 text-sm mb-4 text-center">{{ error }}</p>

        <button
          @click="handleGoogleLogin"
          :disabled="loading"
          class="w-full flex items-center justify-center gap-3 py-2.5 bg-white border border-verse-slate/20 rounded-lg font-medium hover:bg-gray-50 transition disabled:opacity-50"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          {{ loading ? 'Signing in...' : 'Sign in with Google' }}
        </button>
      </div>

      <div class="flex justify-center mt-6 gap-1.5">
        <span v-for="i in 5" :key="i" class="w-1.5 h-1.5 rounded-full bg-verse-slate/20" />
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Create auth/callback.vue**

Create `frontend/app/pages/auth/callback.vue`:

```vue
<script setup lang="ts">
import { useSupabaseClient } from '~/utils/supabase'

definePageMeta({ layout: false })

const { fetchUser } = useAuth()
const error = ref('')

onMounted(async () => {
  try {
    const supabase = useSupabaseClient()

    // Supabase will parse the hash fragment automatically
    const { error: authError } = await supabase.auth.getSession()
    if (authError) throw authError

    await fetchUser()

    const { user } = useAuth()
    if (user.value?.has_partner) {
      navigateTo('/rules')
    } else {
      navigateTo('/invite')
    }
  } catch (e: any) {
    error.value = e.message || 'Authentication failed'
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-verse-bg">
    <div class="text-center">
      <p v-if="error" class="text-red-500">{{ error }}</p>
      <p v-else class="text-verse-slate">Signing you in...</p>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Create invite.vue**

Create `frontend/app/pages/invite.vue`:

```vue
<script setup lang="ts">
definePageMeta({ layout: false })

const { api } = useApi()
const { user, fetchUser, logout } = useAuth()

const inviteCode = ref('')
const generatedCode = ref('')
const error = ref('')
const loading = ref(false)
const mode = ref<'choose' | 'create' | 'accept'>('choose')

async function createInvite() {
  loading.value = true
  error.value = ''
  try {
    const data = await api<{ code: string }>('/auth/invite', { method: 'POST' })
    generatedCode.value = data.code
    mode.value = 'create'
  } catch (e: any) {
    error.value = e?.data?.detail || 'Failed to create invite'
  } finally {
    loading.value = false
  }
}

async function acceptInvite() {
  if (!inviteCode.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    await api('/auth/accept-invite', {
      method: 'POST',
      body: { code: inviteCode.value.trim() },
    })
    await fetchUser()
    navigateTo('/rules')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Invalid or expired invite code'
  } finally {
    loading.value = false
  }
}

async function copyCode() {
  await navigator.clipboard.writeText(generatedCode.value)
}

// If user already has partner, redirect
onMounted(async () => {
  await fetchUser()
  if (user.value?.has_partner) {
    navigateTo('/rules')
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-verse-bg">
    <div class="w-full max-w-sm mx-4">
      <div class="text-center mb-8">
        <h1 class="text-4xl font-serif text-verse-text tracking-wide">Verse</h1>
        <p class="text-verse-slate text-sm mt-2 font-light">Connect with your partner</p>
      </div>

      <div class="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-8 border border-verse-slate/10">
        <!-- Choose mode -->
        <div v-if="mode === 'choose'" class="space-y-4">
          <p class="text-sm text-verse-text text-center mb-4">Welcome, {{ user?.display_name }}! To get started, invite your partner or enter their invite code.</p>

          <button
            @click="createInvite"
            :disabled="loading"
            class="w-full py-2.5 bg-verse-slate text-white rounded-lg font-medium hover:bg-verse-slate/90 transition disabled:opacity-50"
          >
            Create invite code
          </button>

          <button
            @click="mode = 'accept'"
            class="w-full py-2.5 border border-verse-slate/20 text-verse-text rounded-lg font-medium hover:bg-gray-50 transition"
          >
            I have an invite code
          </button>
        </div>

        <!-- Show generated code -->
        <div v-else-if="mode === 'create'" class="space-y-4">
          <p class="text-sm text-verse-text text-center">Share this code with your partner:</p>
          <div class="flex items-center gap-2">
            <code class="flex-1 bg-gray-100 px-4 py-2.5 rounded-lg text-center font-mono text-lg tracking-wider">{{ generatedCode }}</code>
            <button @click="copyCode" class="px-3 py-2.5 bg-verse-slate text-white rounded-lg hover:bg-verse-slate/90 transition text-sm">
              Copy
            </button>
          </div>
          <p class="text-xs text-verse-slate text-center">Valid for 7 days. Waiting for your partner to enter this code.</p>
          <button @click="mode = 'choose'" class="w-full py-2 text-sm text-verse-slate hover:underline">Back</button>
        </div>

        <!-- Enter invite code -->
        <div v-else-if="mode === 'accept'" class="space-y-4">
          <p class="text-sm text-verse-text text-center">Enter the invite code from your partner:</p>
          <input
            v-model="inviteCode"
            type="text"
            placeholder="Paste invite code"
            class="w-full px-4 py-2.5 rounded-lg border border-verse-slate/20 bg-white focus:outline-none focus:ring-2 focus:ring-verse-slate/40 transition font-mono text-center tracking-wider"
          />
          <p v-if="error" class="text-red-500 text-sm text-center">{{ error }}</p>
          <button
            @click="acceptInvite"
            :disabled="loading || !inviteCode.trim()"
            class="w-full py-2.5 bg-verse-slate text-white rounded-lg font-medium hover:bg-verse-slate/90 transition disabled:opacity-50"
          >
            {{ loading ? 'Connecting...' : 'Connect' }}
          </button>
          <button @click="mode = 'choose'" class="w-full py-2 text-sm text-verse-slate hover:underline">Back</button>
        </div>
      </div>

      <div class="text-center mt-4">
        <button @click="logout" class="text-sm text-verse-slate hover:underline">Sign out</button>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 4: Replace plugins/auth.ts**

Replace `frontend/app/plugins/auth.ts` with:

```typescript
import { useSupabaseClient } from '~/utils/supabase'

export default defineNuxtPlugin(async () => {
  const supabase = useSupabaseClient()
  const { fetchUser } = useAuth()

  const { data } = await supabase.auth.getSession()
  if (data.session) {
    await fetchUser()
  }

  supabase.auth.onAuthStateChange(async (event) => {
    if (event === 'SIGNED_IN') {
      await fetchUser()
    } else if (event === 'SIGNED_OUT') {
      const { user } = useAuth()
      user.value = null
    }
  })
})
```

- [ ] **Step 5: Replace middleware/auth.global.ts**

Replace `frontend/app/middleware/auth.global.ts` with:

```typescript
export default defineNuxtRouteMiddleware((to) => {
  const { isAuthenticated, hasPartner } = useAuth()

  const publicPages = ['/login', '/auth/callback']
  if (publicPages.includes(to.path)) {
    if (isAuthenticated.value && hasPartner.value) {
      return navigateTo('/rules')
    }
    return
  }

  if (to.path === '/invite') {
    if (!isAuthenticated.value) {
      return navigateTo('/login')
    }
    if (hasPartner.value) {
      return navigateTo('/rules')
    }
    return
  }

  if (!isAuthenticated.value) {
    return navigateTo('/login')
  }

  if (!hasPartner.value) {
    return navigateTo('/invite')
  }
})
```

- [ ] **Step 6: Commit**

```bash
cd frontend && git add app/pages/login.vue app/pages/auth/callback.vue app/pages/invite.vue app/plugins/auth.ts app/middleware/auth.global.ts
git commit -m "feat: add Google OAuth login, invite page, and auth callback"
```

---

## Task 9: Frontend — Update Components for Schema Changes

**Files:**
- Modify: any component that references `username` (now `display_name` or `email`)

- [ ] **Step 1: Search for username references in frontend**

```bash
cd frontend && grep -rn "username" app/ --include="*.vue" --include="*.ts"
```

Update any references from `username` to `display_name` (for display) or `email` (for identity). The main places will be:
- Components displaying answer/note authors (previously `username`, now `display_name`)
- Any component using `user.username` (now `user.email` or `user.display_name`)

- [ ] **Step 2: Fix each reference found**

For each file found in Step 1, update the property name. This is a search-and-replace within the frontend components.

- [ ] **Step 3: Verify frontend builds**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 4: Commit**

```bash
cd frontend && git add -A
git commit -m "feat: update frontend components for new schema (username -> display_name)"
```

---

## Task 10: Docker and Deployment Config

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Update docker-compose.yml**

Replace `docker-compose.yml` with:

```yaml
services:
  backend:
    build: ./backend
    container_name: verse-backend
    ports:
      - "8742:8000"
    depends_on:
      - tunnel
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET}
      - CORS_ORIGINS=${BACKEND_CORS_ORIGINS:-http://localhost:3742}
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      args:
        NUXT_PUBLIC_API_BASE: ${NUXT_PUBLIC_API_BASE:-https://verse-api.alifpunya.com}
        NUXT_PUBLIC_SUPABASE_URL: ${SUPABASE_URL}
        NUXT_PUBLIC_SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
    container_name: verse-frontend
    ports:
      - "3742:3000"
    depends_on:
      - backend
      - tunnel
    restart: unless-stopped

  tunnel:
    image: cloudflare/cloudflared:latest
    container_name: verse-tunnel
    restart: always
    command: tunnel --no-autoupdate run --token ${TUNNEL_TOKEN}
```

Changes: removed `db-data` volume, replaced `BACKEND_DATABASE_URL` with `DATABASE_URL`, added Supabase env vars.

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: update docker-compose for Supabase (remove SQLite volume, add env vars)"
```

---

## Task 11: Supabase Setup Documentation

**Files:**
- Create: `docs/supabase-setup.md`

- [ ] **Step 1: Create setup guide**

Create `docs/supabase-setup.md`:

```markdown
# Supabase Setup Guide

## 1. Create Supabase Project

1. Go to https://supabase.com and create a new project
2. Note down:
   - Project URL (e.g., `https://xxxx.supabase.co`)
   - Anon/public key (from Settings > API)
   - JWT Secret (from Settings > API > JWT Settings)
   - Database connection string (from Settings > Database > Connection string > URI)

## 2. Enable Google Auth

1. In Supabase dashboard: Authentication > Providers > Google
2. Enable Google provider
3. Add your Google OAuth client ID and secret
   - Create these at https://console.cloud.google.com/apis/credentials
   - Authorized redirect URI: `https://<your-supabase-url>/auth/v1/callback`
4. Save

## 3. Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_JWT_SECRET=<jwt-secret>
BACKEND_CORS_ORIGINS=http://localhost:3742,https://verse.alifpunya.com
NUXT_PUBLIC_API_BASE=https://verse-api.alifpunya.com
TUNNEL_TOKEN=<cloudflare-tunnel-token>
```

## 4. Google Cloud Console

1. Create OAuth 2.0 Client ID (Web application)
2. Authorized JavaScript origins: your frontend URL
3. Authorized redirect URIs: `https://<supabase-url>/auth/v1/callback`
```

- [ ] **Step 2: Commit**

```bash
git add docs/supabase-setup.md
git commit -m "docs: add Supabase setup guide"
```

---

## Task 12: Final Integration Test

- [ ] **Step 1: Run backend tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Build frontend**

```bash
cd frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 3: Verify no old imports remain**

```bash
grep -rn "from app.auth import\|from app.seed import\|python-jose\|passlib\|bcrypt" backend/ --include="*.py" --include="*.txt"
```

Expected: No matches (all old auth references removed).

```bash
grep -rn "verse-token\|verse-refresh-token\|OAuth2Password" frontend/app/ --include="*.ts" --include="*.vue"
```

Expected: No matches (all old cookie/token references removed).

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup for Supabase migration"
```
