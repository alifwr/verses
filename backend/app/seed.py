from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_users(db: Session) -> None:
    alif = db.query(User).filter(User.username == "alif").first()
    syifa = db.query(User).filter(User.username == "syifa").first()

    if alif and syifa:
        return

    hashed_password = pwd_context.hash("verse2024")

    if not alif:
        alif = User(
            username="alif",
            display_name="Alif",
            hashed_password=hashed_password,
        )
        db.add(alif)

    if not syifa:
        syifa = User(
            username="syifa",
            display_name="Syifa",
            hashed_password=hashed_password,
        )
        db.add(syifa)

    db.flush()

    alif.partner_id = syifa.id
    syifa.partner_id = alif.id

    db.commit()
