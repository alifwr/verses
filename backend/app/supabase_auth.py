import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

security = HTTPBearer()


def decode_supabase_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_supabase_jwt(credentials.credentials)
    supabase_uid = payload.get("sub")
    if not supabase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
    if user is None:
        # Auto-create user on first login
        email = payload.get("email", "")
        user_metadata = payload.get("user_metadata", {})
        display_name = user_metadata.get("full_name") or user_metadata.get("name") or email.split("@")[0]
        avatar_url = user_metadata.get("avatar_url") or user_metadata.get("picture")

        user = User(
            supabase_uid=supabase_uid,
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
