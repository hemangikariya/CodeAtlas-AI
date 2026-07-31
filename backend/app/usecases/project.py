from typing import List, Optional
from fastapi import HTTPException, status

from backend.app.adapters.repositories.project_repository import ProjectRepository
from backend.app.domain.models import Project
from backend.app.schemas.project import ProjectCreate, ProjectUpdate

class CreateProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def execute(self, project_in: ProjectCreate) -> Project:
        new_project = Project(
            name=project_in.name,
            description=project_in.description
        )
        return await self.project_repo.create_project(new_project)

class GetProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def execute(self, project_id: str) -> Project:
        project = await self.project_repo.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found."
            )
        return project

class GetAllProjectsUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def execute(self, skip: int = 0, limit: int = 100) -> List[Project]:
        return await self.project_repo.get_all_projects(skip=skip, limit=limit)

class UpdateProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def execute(self, project_id: str, project_in: ProjectUpdate) -> Project:
        project = await self.project_repo.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found."
            )
        updated_project = await self.project_repo.update_project(
            project_id=project_id,
            name=project_in.name,
            description=project_in.description
        )
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found."
            )
        return updated_project

class DeleteProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def execute(self, project_id: str) -> Project:
        project = await self.project_repo.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found."
            )
        deleted = await self.project_repo.delete_project(project_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found."
            )
        return deleted
