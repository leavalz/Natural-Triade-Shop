from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator('password')
    def password_strength(cls,v):
        if not any(c.isupper() for c in v):
            raise ValueError('La clave debe tener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('La clave debe tener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La clave debe tener al menos un número')
        return v
    
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes= True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"