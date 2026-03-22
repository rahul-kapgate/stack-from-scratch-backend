from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserType


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    user_type: UserType
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)