from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from backend.app.adapters.models.project_model import ProjectModel
from backend.app.adapters.repositories.base_repository import BaseRepository
from backend.app.domain.models import Project

class ProjectRepository(BaseRepository[ProjectModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(ProjectModel, db)

    def _to_domain(self, model: ProjectModel) -> Project:
        return Project(
            id=str(model.id),
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_project(self, project_id: str) -> Optional[Project]:
        try:
            uid = uuid.UUID(project_id)
        except ValueError:
            return None
        project_model = await self.get(uid)
        if project_model:
            return self._to_domain(project_model)
        return None

    async def get_all_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        project_models = await self.get_multi(skip=skip, limit=limit)
        return [self._to_domain(m) for m in project_models]

    async def create_project(self, project: Project) -> Project:
        db_project = ProjectModel(
            id=uuid.UUID(project.id),
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        created_db_project = await self.create(db_project)
        return self._to_domain(created_db_project)

    async def update_project(self, project_id: str, name: str, description: Optional[str]) -> Optional[Project]:
        try:
            uid = uuid.UUID(project_id)
        except ValueError:
            return None
        project_model = await self.get(uid)
        if project_model:
            project_model.name = name
            project_model.description = description
            await self.db.flush()
            return self._to_domain(project_model)
        return None

    async def delete_project(self, project_id: str) -> Optional[Project]:
        try:
            uid = uuid.UUID(project_id)
        except ValueError:
            return None
        removed_model = await self.remove(uid)
        if removed_model:
            return self._to_domain(removed_model)
        return None
