from enum import Enum

from sqlalchemy import String, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserType(str, Enum):
    student = "student"
    professional = "professional"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    user_type: Mapped[UserType] = mapped_column(SqlEnum(UserType), nullable=False, default=UserType.student)