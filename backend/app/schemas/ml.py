from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class MLPredictionRequest(BaseModel):
    repository_id: str = Field(..., description="ID of target repository")
    snapshot_id: str = Field(..., description="ID of snapshot to query features for")


class MLPredictionResponse(BaseModel):
    prediction: float = Field(..., description="Calculated prediction score or classification label")
    confidence: float = Field(..., description="Confidence margin or R² baseline score")
    top_features: List[str] = Field(..., description="Top 3 features explaining the prediction result")
    prediction_type: str = Field(..., description="Metric name (maintainability, bug-risk, etc.)")
    model_version: str = Field(..., description="Version of model used for inference")
    created_at: str = Field(..., description="Timestamp of inference run")


class MLModelListItem(BaseModel):
    id: str
    model_name: str
    version: str
    algorithm: str
    dataset: Optional[str] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    created_at: str
