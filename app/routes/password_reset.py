from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controller.password_reset_controller import (
    forgot_password_controller,
    reset_password_controller,
)
from app.core.database import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    return forgot_password_controller(db=db, payload=payload)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    return reset_password_controller(db=db, payload=payload)