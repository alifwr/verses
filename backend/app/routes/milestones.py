from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import nulls_last
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Milestone, MilestoneApproval, User
from app.schemas import MilestoneCreate, MilestoneOut, MilestoneUpdate

router = APIRouter(prefix="/milestones", tags=["milestones"])


def milestone_to_out(milestone: Milestone, current_user_id: int, partner_id: int | None) -> MilestoneOut:
    approver_ids = [approval.user_id for approval in milestone.approvals]
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
        is_approved_by_partner=partner_id in approver_ids if partner_id is not None else False,
        created_at=milestone.created_at,
    )


@router.get("", response_model=list[MilestoneOut])
def list_milestones(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    milestones = (
        db.query(Milestone)
        .order_by(nulls_last(Milestone.target_date.asc()), Milestone.created_at.desc())
        .all()
    )
    partner_id = current_user.partner_id
    return [milestone_to_out(m, current_user.id, partner_id) for m in milestones]


@router.post("", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
def create_milestone(
    body: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    milestone = Milestone(
        title=body.title,
        description=body.description,
        target_date=body.target_date,
        proposed_by=current_user.id,
    )
    db.add(milestone)
    db.flush()

    # Auto-approve for proposer
    approval = MilestoneApproval(milestone_id=milestone.id, user_id=current_user.id)
    db.add(approval)

    db.commit()
    db.refresh(milestone)
    partner_id = current_user.partner_id
    return milestone_to_out(milestone, current_user.id, partner_id)


@router.post("/{milestone_id}/approve", response_model=MilestoneOut)
def approve_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if milestone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    existing = (
        db.query(MilestoneApproval)
        .filter(MilestoneApproval.milestone_id == milestone_id, MilestoneApproval.user_id == current_user.id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already approved")
    approval = MilestoneApproval(milestone_id=milestone_id, user_id=current_user.id)
    db.add(approval)
    db.commit()
    db.refresh(milestone)

    if len(milestone.approvals) >= 2 and not milestone.is_confirmed:
        milestone.is_confirmed = True
        db.commit()
        db.refresh(milestone)

    partner_id = current_user.partner_id
    return milestone_to_out(milestone, current_user.id, partner_id)


@router.patch("/{milestone_id}", response_model=MilestoneOut)
def update_milestone(
    milestone_id: int,
    body: MilestoneUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if milestone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

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
    partner_id = current_user.partner_id
    return milestone_to_out(milestone, current_user.id, partner_id)


@router.delete("/{milestone_id}", response_model=MilestoneOut)
def delete_milestone(
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
    if milestone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    if milestone.proposed_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the proposer can delete this milestone")

    if milestone.is_confirmed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a confirmed milestone")

    partner_id = current_user.partner_id
    out = milestone_to_out(milestone, current_user.id, partner_id)
    db.delete(milestone)
    db.commit()
    return out
