from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate


def create_user_controller(db: Session, payload: UserCreate) -> User:
    # check if email already exists
    existing_user = db.scalar(
        select(User).where(User.email == payload.email)
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # check if phone already exists
    existing_phone = db.scalar(
        select(User).where(User.phone == payload.phone)
    )
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone already registered",
        )

    # create new user
    new_user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password=get_password_hash(payload.password),
        user_type=payload.user_type,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

def get_all_users_controller(db: Session):
    users = db.scalars(select(User).order_by(User.id.desc())).all()
    return users