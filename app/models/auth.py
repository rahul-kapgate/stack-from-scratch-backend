from enum import Enum

from sqlalchemy import String, Enum as SqlEnum, DateTime, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.user import UserType


class AuthRequestStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    expired = "expired"


class AuthRequest(Base):
    __tablename__ = "auth_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    user_type: Mapped[UserType] = mapped_column(
        SqlEnum(UserType), nullable=False, default=UserType.student
    )

    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    otp_expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    otp_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[AuthRequestStatus] = mapped_column(
        SqlEnum(AuthRequestStatus),
        nullable=False,
        default=AuthRequestStatus.pending,
    )
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )