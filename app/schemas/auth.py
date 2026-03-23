from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserType


class SendOtpRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6, max_length=72)
    user_type: UserType


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., pattern=r"^\d{6}$")


class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=72)


class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    identifier: str = Field(..., min_length=3, max_length=255)

class ResetPasswordRequest(BaseModel):
    identifier: str = Field(..., min_length=3, max_length=255)
    otp: str = Field(..., pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=6, max_length=72)
    confirm_password: str = Field(..., min_length=6, max_length=72)
    
class SendOtpResponse(BaseModel):
    message: str
    email: EmailStr


class VerifyOtpResponse(BaseModel):
    message: str
    user_id: int
    email: EmailStr


class TokenResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    name: str
    email: EmailStr
    phone: str
    user_type: UserType


class MessageResponse(BaseModel):
    message: str