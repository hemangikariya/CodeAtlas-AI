import os
import pickle
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("codeatlas.ml")


class ModelRegistry:
    """
    Manages filesystem serialization, loading, and versioning of trained model pipelines, 
    along with metadata logs and evaluation metric reports.
    """

    def __init__(self, base_dir: str = "backend/data/models"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_model_dir(self, model_name: str, version: str) -> str:
        return os.path.join(self.base_dir, model_name, version)

    def save_model(
        self,
        model_name: str,
        version: str,
        pipeline: Any,
        metadata: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> None:
        """
        Saves model pipeline (weights + scaler mean/std) and JSON metadata to disk.
        """
        model_dir = self._get_model_dir(model_name, version)
        os.makedirs(model_dir, exist_ok=True)

        # 1. Serialize model pipeline
        pkl_path = os.path.join(model_dir, "model.pkl")
        try:
            with open(pkl_path, "wb") as f:
                pickle.dump(pipeline, f)
        except Exception as e:
            logger.error(f"Failed to serialize pipeline for {model_name} v{version}: {str(e)}")
            raise e

        # 2. Write metadata.json
        meta_path = os.path.join(model_dir, "metadata.json")
        full_meta = {
            "model_name": model_name,
            "version": version,
            "created_at": datetime.utcnow().isoformat() + "Z",
            **metadata
        }
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(full_meta, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write metadata for {model_name} v{version}: {str(e)}")

        # 3. Write metrics.json
        metrics_path = os.path.join(model_dir, "metrics.json")
        try:
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write metrics for {model_name} v{version}: {str(e)}")

        # 4. Write feature_schema.json
        schema_path = os.path.join(model_dir, "feature_schema.json")
        from backend.app.ml.dataset_builder import DatasetBuilder
        try:
            with open(schema_path, "w", encoding="utf-8") as f:
                json.dump({"features": DatasetBuilder.FEATURE_COLS}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write feature schema for {model_name}: {str(e)}")

        logger.info(f"Successfully registered model {model_name} version {version}")

    def load_model(self, model_name: str, version: str) -> Tuple[Any, Dict[str, Any], Dict[str, Any]]:
        """
        Loads model pipeline binary, metadata, and metric details.
        """
        model_dir = self._get_model_dir(model_name, version)
        pkl_path = os.path.join(model_dir, "model.pkl")
        meta_path = os.path.join(model_dir, "metadata.json")
        metrics_path = os.path.join(model_dir, "metrics.json")

        if not os.path.exists(pkl_path):
            raise FileNotFoundError(f"Model pipeline not found: {pkl_path}")

        try:
            with open(pkl_path, "rb") as f:
                pipeline = pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to deserialize pipeline for {model_name} v{version}: {str(e)}")
            raise e

        metadata = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.error(f"Failed to read metadata for {model_name} v{version}: {str(e)}")

        metrics = {}
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r", encoding="utf-8") as f:
                    metrics = json.load(f)
            except Exception as e:
                logger.error(f"Failed to read metrics for {model_name} v{version}: {str(e)}")

        return pipeline, metadata, metrics

    def list_versions(self, model_name: str) -> List[str]:
        path = os.path.join(self.base_dir, model_name)
        if not os.path.exists(path):
            return []
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

    def get_latest_version(self, model_name: str) -> Optional[str]:
        versions = self.list_versions(model_name)
        if not versions:
            return None
        # Sort version strings semantically or chronologically (assuming v1, v2 format or basic sorting)
        versions.sort()
        return versions[-1]


# Singleton instance
model_registry = ModelRegistry()
