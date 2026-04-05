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
