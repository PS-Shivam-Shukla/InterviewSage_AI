"""
Authentication routes — register, login, get current user.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    AuthResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.
    
    Returns JWT token and user information on success.
    """
    auth_service = AuthService(db)

    # Attempt registration
    user = auth_service.register_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create token
    token = auth_service.create_user_token(user)
    user_response = auth_service.user_to_response(user)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=user_response,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login and get access token",
)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login with email and password.
    
    Returns JWT token and user information on success.
    """
    auth_service = AuthService(db)

    # Authenticate user
    user = auth_service.authenticate_user(
        email=request.email,
        password=request.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create token
    token = auth_service.create_user_token(user)
    user_response = auth_service.user_to_response(user)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=user_response,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Get information about the currently authenticated user.
    
    Requires valid JWT token in Authorization header.
    """
    return UserResponse.model_validate(current_user)
