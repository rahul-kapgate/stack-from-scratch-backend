from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserType


class SendOtpRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)
    user_type: UserType


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class MessageResponse(BaseModel):
    message: str


class SendOtpResponse(BaseModel):
    message: str
    email: EmailStr


class VerifyOtpResponse(BaseModel):
    message: str
    user_id: int
    email: EmailStr