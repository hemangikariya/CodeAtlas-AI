from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uvicorn

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.adapters.database.base import get_db
from backend.app.api.v1 import api_router

# Setup system logs
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CodeAtlas AI Enterprise API Platform",
    version="0.1.0-alpha",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", status_code=status.HTTP_200_OK, tags=["system"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Check core system component statuses.
    """
    db_status = "unhealthy"
    try:
        # Check database connection viability
        await db.execute(select(1))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Health check failed database connectivity: {str(e)}")
        
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "components": {
            "database": db_status
        }
    }

@app.get("/ready", status_code=status.HTTP_200_OK, tags=["system"])
async def ready_check():
    """
    Confirm application initialization readiness.
    """
    return {"status": "ready"}

@app.get("/version", status_code=status.HTTP_200_OK, tags=["system"])
async def version_info():
    """
    Return active platform release configuration.
    """
    return {
        "version": "0.1.0-alpha",
        "phase": "Phase 1 - Foundation"
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
