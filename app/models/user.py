"""
User models for the Clinical Trials & FDA Data Search App.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr

class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=8)

class UserLogin(UserBase):
    """User login model."""
    password: str

class User(UserBase):
    """User model."""
    id: str
    created_at: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
