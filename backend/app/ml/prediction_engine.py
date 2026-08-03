import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# Features & Inferences
from backend.app.ml.feature_engineering import FeatureExtractor
from backend.app.ml.feature_store import feature_store
from backend.app.ml.inference import InferenceEngine
from backend.app.ml.model_registry import model_registry
from backend.app.ml.training import ModelTrainer

# DB model
from backend.app.adapters.models.prediction_history_model import PredictionHistoryModel

logger = logging.getLogger("codeatlas.ml")


class PredictionEngine:
    """
    Coordinates repository lookup, cached feature retrieval, model inference, 
    explainability generation, and historical database logging.
    """

    @staticmethod
    async def predict_metric(
        db: AsyncSession,
        repository_id: str,
        snapshot_id: str,
        prediction_type: str,
        version: str = "v1"
    ) -> Dict[str, Any]:
        """
        Extracts snapshot features, runs inference, saves database records, 
        and returns explainable predictive reports.
        """
        # 1. Fetch cached features or compute them
        features = feature_store.get(snapshot_id)
        if not features:
            logger.info(f"Features cache miss for {snapshot_id}. Computing...")
            features = await FeatureExtractor.extract_features(db, snapshot_id)
            feature_store.set(snapshot_id, features)

        # 2. Check if model is registered. If missing, trigger auto cold-start training!
        latest_ver = model_registry.get_latest_version(prediction_type)
        if not latest_ver:
            logger.warning(f"No trained model registered for '{prediction_type}'. Triggering cold-start training...")
            await ModelTrainer.train_all_models(db)
            latest_ver = "v1"

        # 3. Execute inference
        prediction, confidence, importances = InferenceEngine.run_inference(
            model_name=prediction_type,
            version=latest_ver,
            features=features
        )

        # 4. Sort and select top 3 features by importances
        sorted_feats = sorted(importances.items(), key=lambda item: item[1], reverse=True)
        top_features = [cls_feat_name(name) for name, _ in sorted_feats[:3]]

        # 5. Log prediction run in DB history
        history_item = PredictionHistoryModel(
            repository_id=uuid.UUID(repository_id) if isinstance(repository_id, str) else repository_id,
            prediction_type=prediction_type,
            prediction=float(prediction),
            confidence=float(confidence),
            model_version=latest_ver
        )
        db.add(history_item)
        await db.commit()
        await db.refresh(history_item)

        return {
            "prediction": float(prediction),
            "confidence": float(confidence),
            "top_features": top_features,
            "prediction_type": prediction_type,
            "model_version": latest_ver,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }


def cls_feat_name(name: str) -> str:
    """
    Formats raw DB metric names into human-readable text for SHAP/explainability reports.
    """
    mapping = {
        "cyclomatic_complexity": "Cyclomatic Complexity",
        "dependency_density": "Dependency Density",
        "avg_func_len": "Average Function Length",
        "code_smells": "Code Smells Count",
        "total_files": "Total Files Count",
        "lines_of_code": "Lines of Code",
        "duplicate_code": "Duplicated Lines Ratio",
        "comment_ratio": "Comment Line Ratio"
    }
    return mapping.get(name, name.replace("_", " ").title())
