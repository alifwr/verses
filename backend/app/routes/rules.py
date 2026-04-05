from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.supabase_auth import get_current_user
from app.database import get_db
from app.models import Rule, RuleSignature, User
from app.schemas import RuleCreate, RuleOut

router = APIRouter(prefix="/rules", tags=["rules"])


def rule_to_out(rule: Rule, current_user_id: int, partner_id: int | None) -> RuleOut:
    signer_ids = [sig.user_id for sig in rule.signatures]
    return RuleOut(
        id=rule.id,
        title=rule.title,
        description=rule.description,
        proposed_by=rule.proposed_by,
        proposer_name=rule.proposer.display_name,
        is_sealed=rule.is_sealed,
        is_agreed_by_me=current_user_id in signer_ids,
        is_agreed_by_partner=partner_id in signer_ids if partner_id is not None else False,
        created_at=rule.created_at,
    )


@router.get("", response_model=list[RuleOut])
def list_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rules = db.query(Rule).order_by(Rule.created_at.desc()).all()
    partner_id = current_user.partner_id
    return [rule_to_out(rule, current_user.id, partner_id) for rule in rules]


@router.post("", response_model=RuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: RuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = Rule(
        title=body.title,
        description=body.description,
        proposed_by=current_user.id,
    )
    db.add(rule)
    db.flush()

    # Auto-sign for proposer
    sig = RuleSignature(rule_id=rule.id, user_id=current_user.id)
    db.add(sig)

    db.commit()
    db.refresh(rule)
    partner_id = current_user.partner_id
    return rule_to_out(rule, current_user.id, partner_id)


@router.post("/{rule_id}/sign", response_model=RuleOut)
def sign_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    # Check if already signed
    existing = (
        db.query(RuleSignature)
        .filter(RuleSignature.rule_id == rule_id, RuleSignature.user_id == current_user.id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already signed")
    signature = RuleSignature(rule_id=rule_id, user_id=current_user.id)
    db.add(signature)
    db.commit()
    db.refresh(rule)

    # Seal if 2 or more signatures
    if len(rule.signatures) >= 2 and not rule.is_sealed:
        rule.is_sealed = True
        db.commit()
        db.refresh(rule)

    partner_id = current_user.partner_id
    return rule_to_out(rule, current_user.id, partner_id)


@router.delete("/{rule_id}", response_model=RuleOut)
def delete_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    if rule.proposed_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the proposer can delete this rule")

    if rule.is_sealed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a sealed rule")

    partner_id = current_user.partner_id
    out = rule_to_out(rule, current_user.id, partner_id)
    db.delete(rule)
    db.commit()
    return out
