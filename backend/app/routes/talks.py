from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import case

from app.auth import get_current_user
from app.database import get_db
from app.models import Talk, TalkNote, User
from app.schemas import TalkCreate, TalkNoteCreate, TalkNoteOut, TalkOut, TalkUpdate

router = APIRouter(prefix="/talks", tags=["talks"])

VALID_STATUSES = {"queued", "discussed", "follow_up"}

STATUS_ORDER = case(
    (Talk.status == "queued", 0),
    (Talk.status == "follow_up", 1),
    (Talk.status == "discussed", 2),
    else_=3,
)


def note_to_out(note: TalkNote) -> TalkNoteOut:
    return TalkNoteOut(
        id=note.id,
        user_id=note.user_id,
        username=note.user.display_name,
        text=note.text,
        created_at=note.created_at,
    )


def talk_to_out(talk: Talk) -> TalkOut:
    return TalkOut(
        id=talk.id,
        title=talk.title,
        description=talk.description,
        proposed_by=talk.proposed_by,
        proposer_name=talk.proposer.display_name,
        status=talk.status,
        queued_for=talk.queued_for,
        notes=[note_to_out(n) for n in talk.notes],
        note_count=len(talk.notes),
        created_at=talk.created_at,
    )


@router.get("", response_model=list[TalkOut])
def list_talks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    talks = (
        db.query(Talk)
        .order_by(STATUS_ORDER, Talk.created_at.desc())
        .all()
    )
    return [talk_to_out(t) for t in talks]


@router.post("", response_model=TalkOut, status_code=status.HTTP_201_CREATED)
def create_talk(
    body: TalkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    talk = Talk(
        title=body.title,
        description=body.description,
        queued_for=body.queued_for,
        proposed_by=current_user.id,
    )
    db.add(talk)
    db.commit()
    db.refresh(talk)
    return talk_to_out(talk)


@router.patch("/{talk_id}", response_model=TalkOut)
def update_talk(
    talk_id: int,
    body: TalkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    talk = db.query(Talk).filter(Talk.id == talk_id).first()
    if talk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talk not found")

    if (body.title is not None or body.description is not None) and talk.proposed_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the proposer can edit title and description")

    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        talk.status = body.status

    if body.title is not None:
        talk.title = body.title
    if body.description is not None:
        talk.description = body.description
    if body.queued_for is not None:
        talk.queued_for = body.queued_for

    db.commit()
    db.refresh(talk)
    return talk_to_out(talk)


@router.delete("/{talk_id}", response_model=TalkOut)
def delete_talk(
    talk_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    talk = db.query(Talk).filter(Talk.id == talk_id).first()
    if talk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talk not found")

    if talk.proposed_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the proposer can delete this talk")

    if talk.status != "queued":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only delete queued talks")

    out = talk_to_out(talk)
    db.delete(talk)
    db.commit()
    return out


@router.post("/{talk_id}/notes", response_model=TalkOut, status_code=status.HTTP_201_CREATED)
def add_note(
    talk_id: int,
    body: TalkNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    talk = db.query(Talk).filter(Talk.id == talk_id).first()
    if talk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talk not found")

    note = TalkNote(
        talk_id=talk_id,
        user_id=current_user.id,
        text=body.text,
    )
    db.add(note)
    db.commit()
    db.refresh(talk)
    return talk_to_out(talk)


@router.delete("/{talk_id}/notes/{note_id}")
def delete_note(
    talk_id: int,
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = db.query(TalkNote).filter(TalkNote.id == note_id, TalkNote.talk_id == talk_id).first()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if note.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only delete your own notes")

    db.delete(note)
    db.commit()
    return {"ok": True}
