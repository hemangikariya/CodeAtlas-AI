from fastapi import HTTPException, status
from datetime import timedelta

from backend.app.adapters.repositories.user_repository import UserRepository
from backend.app.domain.models import User
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.schemas.user import UserCreate, Token

class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, user_in: UserCreate) -> User:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system.",
            )
        
        role = user_in.role if user_in.role in ["ADMIN", "DEVELOPER"] else "DEVELOPER"
        
        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            role=role
        )
        return await self.user_repo.create_user(new_user)

class LoginUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, email: str, password: str) -> Token:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user",
            )
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password",
            )
        
        access_token = create_access_token(subject=user.id)
        return Token(access_token=access_token, token_type="bearer")
