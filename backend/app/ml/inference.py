import numpy as np
import logging
from typing import Dict, Any, Tuple
from backend.app.ml.model_registry import model_registry
from backend.app.ml.preprocessing import FeaturePreprocessor
from backend.app.ml.dataset_builder import DatasetBuilder

logger = logging.getLogger("codeatlas.ml")


class InferenceEngine:
    """
    Handles scaling normalization, inference runs, confidence computation, 
    and feature importance analysis.
    """

    @staticmethod
    def run_inference(
        model_name: str,
        version: str,
        features: Dict[str, Any]
    ) -> Tuple[float, float, Dict[str, float]]:
        """
        Runs prediction for the specified model and features.
        Returns (prediction, confidence, feature_importances).
        """
        # 1. Load pipeline and configuration from registry
        pipeline, metadata, metrics = model_registry.load_model(model_name, version)

        # 2. Preprocess & validate features
        FeaturePreprocessor.validate_features(features)
        vector = FeaturePreprocessor.to_vector(features).reshape(1, -1)

        # 3. Predict & compute confidence
        if model_name == "bug-risk":
            # Classification
            pred_class = pipeline.predict(vector)[0]
            prob = pipeline.predict_proba(vector)[0]
            prediction = float(pred_class)
            confidence = float(prob[int(pred_class)])
        else:
            # Regression
            pred_val = pipeline.predict(vector)[0]
            prediction = float(pred_val)
            # R2 accuracy metric serves as inference confidence baseline
            confidence = float(metadata.get("accuracy", 0.90))

        # 4. Feature importance mappings
        raw_importances = pipeline.model.feature_importances_
        feature_importances = {}
        for col, imp in zip(DatasetBuilder.FEATURE_COLS, raw_importances):
            feature_importances[col] = float(imp)

        return prediction, confidence, feature_importances
