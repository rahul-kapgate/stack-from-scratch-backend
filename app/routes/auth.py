from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controller.auth_controller import (
    send_otp_controller,
    verify_otp_controller,
)
from app.core.database import get_db
from app.schemas.auth import (
    SendOtpRequest,
    SendOtpResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/send-otp",
    response_model=SendOtpResponse,
    status_code=status.HTTP_200_OK,
)
def send_otp(
    payload: SendOtpRequest,
    db: Session = Depends(get_db),
):
    return send_otp_controller(db=db, payload=payload)


@router.post(
    "/verify-otp",
    response_model=VerifyOtpResponse,
    status_code=status.HTTP_201_CREATED,
)
def verify_otp(
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db),
):
    return verify_otp_controller(db=db, payload=payload)