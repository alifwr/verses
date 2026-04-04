from datetime import datetime, date, timezone, timedelta
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

GMT7 = timezone(timedelta(hours=7))


def now_gmt7() -> datetime:
    return datetime.now(GMT7)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)

    partner: Mapped[Optional["User"]] = relationship("User", remote_side="User.id", foreign_keys=[partner_id])
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_gmt7)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")


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
