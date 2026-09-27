from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "STUDENT"
    department_id: int | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    department_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)