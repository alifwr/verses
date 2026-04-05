from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.supabase_auth import get_current_user
from app.database import get_db
from app.models import Answer, Question, User
from app.schemas import AnswerCreate, AnswerOut, QuestionCreate, QuestionOut

router = APIRouter(prefix="/questions", tags=["questions"])


def answer_to_out(answer: Answer) -> AnswerOut:
    return AnswerOut(
        id=answer.id,
        user_id=answer.user_id,
        display_name=answer.user.display_name,
        text=answer.text,
        created_at=answer.created_at,
    )


def question_to_out(question: Question, current_user_id: int, partner_id: int | None) -> QuestionOut:
    my_answer = None
    partner_answer = None

    for ans in question.answers:
        if ans.user_id == current_user_id:
            my_answer = answer_to_out(ans)
        elif ans.user_id == partner_id:
            partner_answer = answer_to_out(ans)

    # Double-blind: hide partner's answer until current user has also answered
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questions = db.query(Question).order_by(Question.created_at.desc()).all()
    partner_id = current_user.partner_id
    return [question_to_out(q, current_user.id, partner_id) for q in questions]


@router.post("", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(
    body: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = Question(
        text=body.text,
        asked_by=current_user.id,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    partner_id = current_user.partner_id
    return question_to_out(question, current_user.id, partner_id)


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    partner_id = current_user.partner_id
    return question_to_out(question, current_user.id, partner_id)


@router.post("/{question_id}/answer", response_model=QuestionOut)
def answer_question(
    question_id: int,
    body: AnswerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    existing = (
        db.query(Answer)
        .filter(Answer.question_id == question_id, Answer.user_id == current_user.id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already answered this question")

    answer = Answer(
        question_id=question_id,
        user_id=current_user.id,
        text=body.text,
    )
    db.add(answer)
    db.commit()
    db.refresh(question)
    partner_id = current_user.partner_id
    return question_to_out(question, current_user.id, partner_id)
