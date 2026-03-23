from enum import Enum

from sqlalchemy import (
    String,
    Enum as SqlEnum,
    DateTime,
    Integer,
    Boolean,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PasswordResetStatus(str, Enum):
    pending = "pending"
    used = "used"
    expired = "expired"


class PasswordResetRequest(Base):
    __tablename__ = "password_reset_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    otp_expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    otp_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    status: Mapped[PasswordResetStatus] = mapped_column(
        SqlEnum(PasswordResetStatus),
        nullable=False,
        default=PasswordResetStatus.pending,
    )

    is_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

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