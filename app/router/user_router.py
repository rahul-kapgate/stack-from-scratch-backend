from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.controller.user_controller import create_user_controller, get_all_users_controller
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    return create_user_controller(db=db, payload=payload)


@router.get(
    "/all-users",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
)
def get_all_users(
    db: Session = Depends(get_db),
): 
    return get_all_users_controller(db=db)