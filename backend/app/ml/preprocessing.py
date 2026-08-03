import numpy as np
from typing import Dict, Any, List, Union, Optional
from backend.app.ml.dataset_builder import DatasetBuilder


class FeaturePreprocessor:
    """
    Handles feature validation, missing value imputation, and scaling 
    using standardization parameters to ensure robust inference.
    """

    FEATURE_COLS = DatasetBuilder.FEATURE_COLS

    @classmethod
    def validate_features(cls, features: Dict[str, Any]) -> None:
        """
        Asserts correctness of incoming feature values.
        Raises ValueError if fields are missing or non-numeric.
        """
        for col in cls.FEATURE_COLS:
            if col not in features:
                raise ValueError(f"Feature validation failed: missing column '{col}'")
            val = features[col]
            if val is None:
                continue
            if not isinstance(val, (int, float)):
                try:
                    float(val)
                except (ValueError, TypeError):
                    raise ValueError(f"Feature validation failed: column '{col}' is not numeric ({val})")

    @classmethod
    def impute_missing(cls, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Fills missing or None values with logical defaults (0.0).
        """
        imputed = {}
        for col in cls.FEATURE_COLS:
            val = features.get(col, 0.0)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                imputed[col] = 0.0
            else:
                imputed[col] = float(val)
        return imputed

    @classmethod
    def to_vector(cls, features: Dict[str, Any]) -> np.ndarray:
        """
        Converts feature dict to structured 1D numpy array in target columns order.
        """
        cls.validate_features(features)
        imputed = cls.impute_missing(features)
        return np.array([imputed[col] for col in cls.FEATURE_COLS], dtype=np.float32)

    @classmethod
    def scale_vector(cls, vector: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
        """
        Performs standardization (x - mean) / std.
        Prevents division by zero by setting zero std to 1.
        """
        safe_std = np.copy(std)
        safe_std[safe_std == 0.0] = 1.0
        return (vector - mean) / safe_std
