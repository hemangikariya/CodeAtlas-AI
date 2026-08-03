import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Auth & Dependencies
from backend.app.core.dependencies import get_db, get_current_active_developer
from backend.app.domain.models import User

# Service & Schemas
from backend.app.ml.ml_service import MLService
from backend.app.schemas.ml import (
    MLPredictionRequest,
    MLPredictionResponse,
    MLModelListItem
)

logger = logging.getLogger("codeatlas.ml")
router = APIRouter()


@router.post("/maintainability", response_model=MLPredictionResponse)
async def predict_maintainability(
    req: MLPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    Predicts code maintainability index score (0 - 100).
    """
    try:
        res = await MLService.get_maintainability(db, req.repository_id, req.snapshot_id)
        return res
    except Exception as e:
        logger.error(f"Error predicting maintainability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/bug-risk", response_model=MLPredictionResponse)
async def predict_bug_risk(
    req: MLPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    Predicts bug risk level (classification 0: low, 1: high).
    """
    try:
        res = await MLService.get_bug_risk(db, req.repository_id, req.snapshot_id)
        return res
    except Exception as e:
        logger.error(f"Error predicting bug risk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/complexity", response_model=MLPredictionResponse)
async def predict_complexity(
    req: MLPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    Predicts code complexity index score (0 - 100).
    """
    try:
        res = await MLService.get_complexity(db, req.repository_id, req.snapshot_id)
        return res
    except Exception as e:
        logger.error(f"Error predicting complexity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/repository-health", response_model=MLPredictionResponse)
async def predict_repository_health(
    req: MLPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    Predicts aggregate repository health score (0 - 100).
    """
    try:
        res = await MLService.get_repository_health(db, req.repository_id, req.snapshot_id)
        return res
    except Exception as e:
        logger.error(f"Error predicting repository health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/models", response_model=List[MLModelListItem])
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    Returns registered models and algorithms metrics in the system.
    """
    try:
        return await MLService.list_models(db)
    except Exception as e:
        logger.error(f"Error listing ML models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/evaluation")
async def get_evaluation(
    current_user: User = Depends(get_current_active_developer)
):
    """
    Loads raw evaluation and hyperparameter training metrics.
    """
    try:
        return await MLService.get_evaluation_metrics()
    except Exception as e:
        logger.error(f"Error loading evaluations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/features")
async def get_features(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    """
    Returns the raw calculated feature vector for a snapshot.
    """
    try:
        return await MLService.get_features(db, snapshot_id)
    except Exception as e:
        logger.error(f"Error getting snapshot features: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
