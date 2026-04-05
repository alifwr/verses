from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app.supabase_auth import get_current_user
from app.database import get_db
from app.models import (
    Answer,
    Milestone,
    MilestoneApproval,
    Question,
    Rule,
    RuleSignature,
    Talk,
    User,
)
from app.schemas import ActivityOut

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityOut])
def get_activity(
    current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)
):
    events: list[ActivityOut] = []

    # Rule events
    rules = db.query(Rule).all()
    for rule in rules:
        events.append(ActivityOut(
            type="rule_created",
            actor=rule.proposer.display_name,
            summary=f'Proposed rule "{rule.title}"',
            timestamp=rule.created_at,
        ))
        for sig in rule.signatures:
            if sig.user_id == rule.proposed_by:
                continue
            events.append(ActivityOut(
                type="rule_sealed" if rule.is_sealed else "rule_signed",
                actor=sig.user.display_name,
                summary=f'Rule "{rule.title}" has been sealed' if rule.is_sealed else f'Signed rule "{rule.title}"',
                timestamp=sig.signed_at,
            ))

    # Question events
    questions = db.query(Question).all()
    for question in questions:
        events.append(ActivityOut(
            type="question_asked",
            actor=question.asker.display_name,
            summary=f'Asked "{question.text[:60]}"',
            timestamp=question.created_at,
        ))
        for answer in question.answers:
            events.append(ActivityOut(
                type="answer_submitted",
                actor=answer.user.display_name,
                summary=f'Answered "{question.text[:40]}..."',
                timestamp=answer.created_at,
            ))
        if len(question.answers) >= 2:
            latest = max(a.created_at for a in question.answers)
            events.append(ActivityOut(
                type="answers_revealed",
                actor="Both",
                summary=f'Answers revealed for "{question.text[:40]}..."',
                timestamp=latest,
            ))

    # Milestone events
    milestones = db.query(Milestone).all()
    for milestone in milestones:
        events.append(ActivityOut(
            type="milestone_proposed",
            actor=milestone.proposer.display_name,
            summary=f'Proposed milestone "{milestone.title}"',
            timestamp=milestone.created_at,
        ))
        for approval in milestone.approvals:
            if approval.user_id == milestone.proposed_by:
                continue
            if milestone.is_confirmed:
                events.append(ActivityOut(
                    type="milestone_confirmed",
                    actor=approval.user.display_name,
                    summary=f'Milestone "{milestone.title}" confirmed',
                    timestamp=approval.approved_at,
                ))
            else:
                events.append(ActivityOut(
                    type="milestone_approved",
                    actor=approval.user.display_name,
                    summary=f'Approved milestone "{milestone.title}"',
                    timestamp=approval.approved_at,
                ))
        if milestone.is_completed:
            events.append(ActivityOut(
                type="milestone_completed",
                actor=milestone.proposer.display_name,
                summary=f'Milestone "{milestone.title}" completed',
                timestamp=milestone.created_at,
            ))

    # Talk events
    talks = db.query(Talk).all()
    for talk in talks:
        events.append(ActivityOut(
            type="talk_queued",
            actor=talk.proposer.display_name,
            summary=f'Queued talk "{talk.title}"',
            timestamp=talk.created_at,
        ))

    events.sort(key=lambda e: e.timestamp, reverse=True)
    return events[:20]
