from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr


class UserType(str, Enum):
    student = "student"
    professional = "professional"


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    user_type: UserType


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    user_type: UserType

    model_config = ConfigDict(from_attributes=True)