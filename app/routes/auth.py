from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controller.auth_controller import (
    send_otp_controller,
    verify_otp_controller,
    login_controller,
    refresh_token_controller,
)
from app.core.database import get_db
from app.schemas.auth import (
    SendOtpRequest,
    SendOtpResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
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


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    return login_controller(db=db, payload=payload)


@router.post(
    "/refresh-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    return refresh_token_controller(db=db, payload=payload)