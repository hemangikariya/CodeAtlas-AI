from fastapi import APIRouter
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.projects import router as projects_router
from backend.app.api.v1.repositories import router as repositories_router
from backend.app.api.v1.knowledge import router as knowledge_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(repositories_router, prefix="/repositories", tags=["repositories"])
api_router.include_router(knowledge_router, tags=["knowledge"])
