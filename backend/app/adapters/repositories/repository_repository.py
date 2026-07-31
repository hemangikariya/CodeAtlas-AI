from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from backend.app.adapters.models.repository_model import RepositoryModel
from backend.app.adapters.repositories.base_repository import BaseRepository
from backend.app.domain.ingestion import Repository

class RepositoryRepository(BaseRepository[RepositoryModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(RepositoryModel, db)

    def _to_domain(self, model: RepositoryModel) -> Repository:
        return Repository(
            id=str(model.id),
            project_id=str(model.project_id),
            name=model.name,
            url=model.url,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_repository(self, repository_id: str) -> Optional[Repository]:
        try:
            uid = uuid.UUID(repository_id)
        except ValueError:
            return None
        model = await self.get(uid)
        if model:
            return self._to_domain(model)
        return None

    async def get_project_repositories(self, project_id: str) -> List[Repository]:
        try:
            pid = uuid.UUID(project_id)
        except ValueError:
            return []
        result = await self.db.execute(select(RepositoryModel).filter(RepositoryModel.project_id == pid))
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def create_repository(self, repo: Repository) -> Repository:
        model = RepositoryModel(
            id=uuid.UUID(repo.id),
            project_id=uuid.UUID(repo.project_id),
            name=repo.name,
            url=repo.url,
            created_at=repo.created_at,
            updated_at=repo.updated_at
        )
        created_model = await self.create(model)
        return self._to_domain(created_model)
