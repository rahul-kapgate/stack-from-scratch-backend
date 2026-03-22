from datetime import datetime, timedelta, timezone
from random import randint

from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.auth import AuthRequest, AuthRequestStatus
from app.models.user import User
from app.schemas.auth import SendOtpRequest, VerifyOtpRequest
from app.services.email_service import send_otp_email


OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(randint(100000, 999999))


def send_otp_controller(db: Session, payload: SendOtpRequest):
    """
    1. Check if user already exists in users table
    2. Expire old pending OTP requests for same email
    3. Save new auth request in auth_requests table
    4. Send OTP email using Resend
    """

    # check if user already exists with same email or phone
    existing_user = db.scalar(
        select(User).where(
            or_(
                User.email == payload.email,
                User.phone == payload.phone,
            )
        )
    )

    if existing_user:
        if existing_user.email == payload.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        if existing_user.phone == payload.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone already registered",
            )

    # expire previous pending requests for same email
    old_requests = db.scalars(
        select(AuthRequest).where(
            AuthRequest.email == payload.email,
            AuthRequest.status == AuthRequestStatus.pending,
            AuthRequest.is_used.is_(False),
        )
    ).all()

    for old_request in old_requests:
        old_request.status = AuthRequestStatus.expired

    # generate otp
    otp = generate_otp()
    otp_hash = get_password_hash(otp)

    # hash password before saving temp data
    hashed_password = get_password_hash(payload.password)

    # create temp auth request record
    auth_request = AuthRequest(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password=hashed_password,
        user_type=payload.user_type,
        otp_hash=otp_hash,
        otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
        otp_attempts=0,
        status=AuthRequestStatus.pending,
        is_used=False,
    )

    db.add(auth_request)
    db.commit()
    db.refresh(auth_request)

    # send otp email
    try:
        send_otp_email(
            to_email=payload.email,
            user_name=payload.name,
            otp=otp,
        )
    except Exception as exc:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to send OTP email: {str(exc)}",
    )

    return {
        "message": "OTP sent successfully to your email",
        "email": payload.email,
    }


def verify_otp_controller(db: Session, payload: VerifyOtpRequest):
    """
    1. Find latest pending auth request by email
    2. Verify otp and expiry
    3. Create final user record in users table
    4. Mark auth request as verified / used
    """

    # get latest pending auth request
    auth_request = db.scalar(
        select(AuthRequest)
        .where(
            AuthRequest.email == payload.email,
            AuthRequest.status == AuthRequestStatus.pending,
            AuthRequest.is_used.is_(False),
        )
        .order_by(AuthRequest.id.desc())
    )

    if not auth_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending OTP request found for this email",
        )

    # check otp expiry
    now = datetime.now(timezone.utc)
    if auth_request.otp_expires_at < now:
        auth_request.status = AuthRequestStatus.expired
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new OTP",
        )

    # check max attempts
    if auth_request.otp_attempts >= MAX_OTP_ATTEMPTS:
        auth_request.status = AuthRequestStatus.expired
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP attempts exceeded. Please request a new OTP",
        )

    # verify otp
    is_valid_otp = verify_password(payload.otp, auth_request.otp_hash)

    if not is_valid_otp:
        auth_request.otp_attempts += 1

        if auth_request.otp_attempts >= MAX_OTP_ATTEMPTS:
            auth_request.status = AuthRequestStatus.expired

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    # final safety check before creating user
    existing_user = db.scalar(
        select(User).where(
            or_(
                User.email == auth_request.email,
                User.phone == auth_request.phone,
            )
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    # create final user record
    new_user = User(
        name=auth_request.name,
        email=auth_request.email,
        phone=auth_request.phone,
        password=auth_request.password,  # already hashed in send_otp_controller
        user_type=auth_request.user_type,
    )

    db.add(new_user)

    # mark auth request as used / verified
    auth_request.status = AuthRequestStatus.verified
    auth_request.is_used = True

    db.commit()
    db.refresh(new_user)

    return {
        "message": "OTP verified successfully. User created",
        "user_id": new_user.id,
        "email": new_user.email,
    }