from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.users import UserRole

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str
    site_id: Optional[int] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
    user_id: Optional[int] = None
    site_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole
    site_id: Optional[int] = None

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    site_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True
