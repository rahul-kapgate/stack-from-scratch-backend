from datetime import datetime, timedelta, timezone
import secrets

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.password_reset import (
    PasswordResetRequest,
    PasswordResetStatus,
)
from app.models.user import User
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from app.services.email_service import send_otp_email


RESET_OTP_EXPIRY_MINUTES = 5
MAX_RESET_OTP_ATTEMPTS = 5
GENERIC_FORGOT_PASSWORD_MESSAGE = (
    "If an account exists, a reset OTP has been sent to the registered email."
)


def generate_secure_otp() -> str:
    """
    Generate a cryptographically secure 6-digit OTP.
    """
    return str(secrets.randbelow(900000) + 100000)


def forgot_password_controller(db: Session, payload: ForgotPasswordRequest):
    """
    Forgot password flow:
    1. Find user by email OR phone
    2. Do not reveal whether user exists
    3. Expire old pending reset requests
    4. Create new password reset request
    5. Send OTP to registered email
    """

    user = db.scalar(
        select(User).where(
            or_(
                User.email == payload.identifier,
                User.phone == payload.identifier,
            )
        )
    )

    # Always return same response to prevent account enumeration
    if not user:
        return {"message": GENERIC_FORGOT_PASSWORD_MESSAGE}

    # Expire older pending requests for this user
    old_requests = db.scalars(
        select(PasswordResetRequest).where(
            PasswordResetRequest.user_id == user.id,
            PasswordResetRequest.status == PasswordResetStatus.pending,
            PasswordResetRequest.is_used.is_(False),
        )
    ).all()

    for old_request in old_requests:
        old_request.status = PasswordResetStatus.expired

    otp = generate_secure_otp()
    otp_hash = get_password_hash(otp)

    reset_request = PasswordResetRequest(
        user_id=user.id,
        email=user.email,
        otp_hash=otp_hash,
        otp_expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=RESET_OTP_EXPIRY_MINUTES),
        otp_attempts=0,
        status=PasswordResetStatus.pending,
        is_used=False,
    )

    try:
        db.add(reset_request)
        db.flush()  # create record in transaction, but do not commit yet

        send_otp_email(
            to_email=user.email,
            user_name=user.name,
            otp=otp,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset OTP email",
        )

    return {"message": GENERIC_FORGOT_PASSWORD_MESSAGE}


def reset_password_controller(db: Session, payload: ResetPasswordRequest):
    """
    Reset password flow:
    1. Find user by email OR phone
    2. Get latest pending reset request
    3. Validate OTP expiry and attempts
    4. Verify OTP
    5. Update password
    6. Mark reset request as used
    """

    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match",
        )

    user = db.scalar(
        select(User).where(
            or_(
                User.email == payload.identifier,
                User.phone == payload.identifier,
            )
        )
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset request",
        )

    reset_request = db.scalar(
        select(PasswordResetRequest)
        .where(
            PasswordResetRequest.user_id == user.id,
            PasswordResetRequest.status == PasswordResetStatus.pending,
            PasswordResetRequest.is_used.is_(False),
        )
        .order_by(PasswordResetRequest.id.desc())
    )

    if not reset_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active password reset request found",
        )

    now = datetime.now(timezone.utc)

    # Check expiry
    if reset_request.otp_expires_at < now:
        reset_request.status = PasswordResetStatus.expired
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one",
        )

    # Check max attempts
    if reset_request.otp_attempts >= MAX_RESET_OTP_ATTEMPTS:
        reset_request.status = PasswordResetStatus.expired
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP attempts exceeded. Please request a new one",
        )

    # Verify OTP
    is_valid_otp = verify_password(payload.otp, reset_request.otp_hash)

    if not is_valid_otp:
        reset_request.otp_attempts += 1

        if reset_request.otp_attempts >= MAX_RESET_OTP_ATTEMPTS:
            reset_request.status = PasswordResetStatus.expired

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    # Update password
    user.password = get_password_hash(payload.new_password)

    # Mark current reset request as used
    reset_request.status = PasswordResetStatus.used
    reset_request.is_used = True

    # Expire any other pending reset requests for same user
    other_pending_requests = db.scalars(
        select(PasswordResetRequest).where(
            PasswordResetRequest.user_id == user.id,
            PasswordResetRequest.status == PasswordResetStatus.pending,
            PasswordResetRequest.is_used.is_(False),
            PasswordResetRequest.id != reset_request.id,
        )
    ).all()

    for request in other_pending_requests:
        request.status = PasswordResetStatus.expired

    db.commit()

    return {"message": "Password reset successful. Please login again."}