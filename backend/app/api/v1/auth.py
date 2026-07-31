from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.core.dependencies import get_user_repository, get_current_user
from backend.app.adapters.repositories.user_repository import UserRepository
from backend.app.schemas.user import UserCreate, UserResponse, Token
from backend.app.usecases.auth import RegisterUserUseCase, LoginUserUseCase
from backend.app.domain.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository)
):
    usecase = RegisterUserUseCase(user_repo)
    return await usecase.execute(user_in)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository)
):
    usecase = LoginUserUseCase(user_repo)
    return await usecase.execute(form_data.username, form_data.password)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
