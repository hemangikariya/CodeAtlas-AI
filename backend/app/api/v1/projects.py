from fastapi import APIRouter, Depends, status
from typing import List

from backend.app.core.dependencies import (
    get_project_repository,
    get_current_active_developer,
    get_current_active_admin
)
from backend.app.adapters.repositories.project_repository import ProjectRepository
from backend.app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from backend.app.usecases.project import (
    CreateProjectUseCase,
    GetProjectUseCase,
    GetAllProjectsUseCase,
    UpdateProjectUseCase,
    DeleteProjectUseCase
)
from backend.app.domain.models import User

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    project_repo: ProjectRepository = Depends(get_project_repository),
    current_user: User = Depends(get_current_active_developer)
):
    usecase = CreateProjectUseCase(project_repo)
    return await usecase.execute(project_in)

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    project_repo: ProjectRepository = Depends(get_project_repository),
    current_user: User = Depends(get_current_active_developer)
):
    usecase = GetAllProjectsUseCase(project_repo)
    return await usecase.execute(skip=skip, limit=limit)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    project_repo: ProjectRepository = Depends(get_project_repository),
    current_user: User = Depends(get_current_active_developer)
):
    usecase = GetProjectUseCase(project_repo)
    return await usecase.execute(project_id)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    project_repo: ProjectRepository = Depends(get_project_repository),
    current_user: User = Depends(get_current_active_developer)
):
    usecase = UpdateProjectUseCase(project_repo)
    return await usecase.execute(project_id, project_in)

@router.delete("/{project_id}", response_model=ProjectResponse)
async def delete_project(
    project_id: str,
    project_repo: ProjectRepository = Depends(get_project_repository),
    current_user: User = Depends(get_current_active_admin)
):
    usecase = DeleteProjectUseCase(project_repo)
    return await usecase.execute(project_id)
