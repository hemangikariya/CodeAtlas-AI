from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from backend.app.adapters.models.user_model import UserModel
from backend.app.adapters.repositories.base_repository import BaseRepository
from backend.app.domain.models import User

class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(UserModel, db)

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=str(model.id),
            email=model.email,
            hashed_password=model.hashed_password,
            role=model.role,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(UserModel).filter(UserModel.email == email))
        user_model = result.scalars().first()
        if user_model:
            return self._to_domain(user_model)
        return None

    async def get_domain_user(self, user_id: str) -> Optional[User]:
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return None
        user_model = await self.get(uid)
        if user_model:
            return self._to_domain(user_model)
        return None

    async def create_user(self, user: User) -> User:
        db_user = UserModel(
            id=uuid.UUID(user.id),
            email=user.email,
            hashed_password=user.hashed_password,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        created_db_user = await self.create(db_user)
        return self._to_domain(created_db_user)
