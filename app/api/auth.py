"""
Authentication module for the Clinical Trials & FDA Data Search App.
Handles user authentication using Supabase.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import httpx
from app.models.user import User, UserCreate, UserLogin

# Initialize router
auth_router = APIRouter()

# Security scheme
security = HTTPBearer()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://sgtguuqbuqtpwmfknovr.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNndGd1dXFidXF0cHdtZmtub3ZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1NjM2NjEsImV4cCI6MjA2MTEzOTY2MX0.CQMb2uuBx7Tf0Flzh5XYiU8VdwlbRqFaZelXSb3xm1I")  # Set this in environment variables

class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    user: User

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate the JWT token from Supabase and return the current user.
    
    Args:
        credentials: The HTTP authorization credentials containing the JWT token.
        
    Returns:
        User: The current authenticated user.
        
    Raises:
        HTTPException: If the token is invalid or expired.
    """
    token = credentials.credentials
    
    # Validate token with Supabase
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_ANON_KEY
            }
        )
        
        if response.status_code != 200:
            # Log the error for debugging
            print(f"Supabase auth error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_data = response.json()
        return User(
            id=user_data.get("id"),
            email=user_data.get("email"),
            created_at=user_data.get("created_at")
        )

@auth_router.post("/register", response_model=TokenResponse)
async def register(user_create: UserCreate):
    """
    Register a new user with email and password.
    
    Args:
        user_create: User registration data.
        
    Returns:
        TokenResponse: Access token and user data.
        
    Raises:
        HTTPException: If registration fails.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/auth/v1/signup",
            headers={"apikey": SUPABASE_ANON_KEY},
            json={"email": user_create.email, "password": user_create.password}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {response.text}"
            )
        
        data = response.json()
        
        return TokenResponse(
            access_token=data.get("access_token"),
            token_type="bearer",
            user=User(
                id=data.get("user", {}).get("id"),
                email=data.get("user", {}).get("email"),
                created_at=data.get("user", {}).get("created_at")
            )
        )

@auth_router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    """
    Login a user with email and password.
    
    Args:
        user_login: User login data.
        
    Returns:
        TokenResponse: Access token and user data.
        
    Raises:
        HTTPException: If login fails.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={"apikey": SUPABASE_ANON_KEY},
            json={"email": user_login.email, "password": user_login.password}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        data = response.json()
        
        return TokenResponse(
            access_token=data.get("access_token"),
            token_type="bearer",
            user=User(
                id=data.get("user", {}).get("id"),
                email=data.get("user", {}).get("email"),
                created_at=data.get("user", {}).get("created_at")
            )
        )

@auth_router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout the current user.
    
    Args:
        credentials: The HTTP authorization credentials containing the JWT token.
        
    Returns:
        dict: Success message.
        
    Raises:
        HTTPException: If logout fails.
    """
    token = credentials.credentials
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/auth/v1/logout",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_ANON_KEY
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logout failed"
            )
        
        return {"message": "Successfully logged out"}
