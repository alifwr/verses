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
