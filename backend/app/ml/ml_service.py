import os
import json
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Engines
from backend.app.ml.prediction_engine import PredictionEngine
from backend.app.ml.training import ModelTrainer
from backend.app.ml.feature_engineering import FeatureExtractor
from backend.app.ml.feature_store import feature_store

# DB models
from backend.app.adapters.models.trained_model_model import TrainedModelModel

logger = logging.getLogger("codeatlas.ml")


class MLService:
    """
    Public Service Facade layer exposing predictions, evaluation metadata, 
    and feature configurations. Other feature modules communicate with the ML 
    Layer exclusively through this interface.
    """

    @staticmethod
    async def get_maintainability(db: AsyncSession, repository_id: str, snapshot_id: str) -> Dict[str, Any]:
        return await PredictionEngine.predict_metric(db, repository_id, snapshot_id, "maintainability")

    @staticmethod
    async def get_bug_risk(db: AsyncSession, repository_id: str, snapshot_id: str) -> Dict[str, Any]:
        return await PredictionEngine.predict_metric(db, repository_id, snapshot_id, "bug-risk")

    @staticmethod
    async def get_complexity(db: AsyncSession, repository_id: str, snapshot_id: str) -> Dict[str, Any]:
        return await PredictionEngine.predict_metric(db, repository_id, snapshot_id, "complexity")

    @staticmethod
    async def get_repository_health(db: AsyncSession, repository_id: str, snapshot_id: str) -> Dict[str, Any]:
        return await PredictionEngine.predict_metric(db, repository_id, snapshot_id, "repository-health")

    @staticmethod
    async def train_all_models(db: AsyncSession) -> Dict[str, Any]:
        return await ModelTrainer.train_all_models(db)

    @staticmethod
    async def list_models(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Returns all trained model entries stored in the database.
        """
        result = await db.execute(select(TrainedModelModel).order_by(TrainedModelModel.created_at.desc()))
        models = result.scalars().all()
        return [
            {
                "id": str(m.id),
                "model_name": m.model_name,
                "version": m.version,
                "algorithm": m.algorithm,
                "dataset": m.dataset,
                "accuracy": m.accuracy,
                "precision": m.precision,
                "recall": m.recall,
                "f1": m.f1,
                "created_at": m.created_at.isoformat() + "Z"
            }
            for m in models
        ]

    @staticmethod
    async def get_evaluation_metrics() -> Dict[str, Any]:
        """
        Loads the evaluation metrics report from the filesystem.
        """
        metrics_path = "backend/app/ml/reports/metrics.json"
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read metrics file: {str(e)}")
        return {"error": "Evaluation report metrics.json not generated yet."}

    @staticmethod
    async def get_features(db: AsyncSession, snapshot_id: str) -> Dict[str, Any]:
        """
        Retrieves cached features or extracts them dynamically for a snapshot.
        """
        features = feature_store.get(snapshot_id)
        if not features:
            logger.info(f"Features cache miss for {snapshot_id} in MLService. Computing...")
            features = await FeatureExtractor.extract_features(db, snapshot_id)
            feature_store.set(snapshot_id, features)
        return features
