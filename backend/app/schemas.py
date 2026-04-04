from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


# --- Auth schemas ---

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

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    partner: Optional[PartnerInfo] = None

    model_config = {"from_attributes": True}


# --- Rules schemas ---

class RuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    emergency_override: bool = False


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
