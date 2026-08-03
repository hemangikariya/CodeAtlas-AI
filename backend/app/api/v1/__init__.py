from fastapi import APIRouter
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.projects import router as projects_router
from backend.app.api.v1.repositories import router as repositories_router
from backend.app.api.v1.knowledge import router as knowledge_router
from backend.app.api.v1.ai import router as ai_router
from backend.app.api.v1.copilot import router as copilot_router
from backend.app.api.v1.ml import router as ml_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(repositories_router, prefix="/repositories", tags=["repositories"])
api_router.include_router(knowledge_router, tags=["knowledge"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(copilot_router, prefix="/copilot", tags=["copilot"])
api_router.include_router(ml_router, prefix="/ml", tags=["ml"])
