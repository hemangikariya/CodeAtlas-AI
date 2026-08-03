import numpy as np
from typing import Dict, Any, Tuple
from backend.app.ml.models.repository_health_model import RepositoryHealthModel
from backend.app.ml.preprocessing import FeaturePreprocessor


class HealthPipeline:
    """
    Standard repository health pipeline orchestrating scaling standardizations and regressors fit/inference.
    """

    def __init__(self, model: RepositoryHealthModel = None, mean: np.ndarray = None, std: np.ndarray = None):
        self.model = model or RepositoryHealthModel()
        self.mean = mean
        self.std = std

    def fit(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        # Calculate mean & std
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0)
        
        # Scale
        X_scaled = FeaturePreprocessor.scale_vector(X, self.mean, self.std)
        self.model.fit(X_scaled, y)
        return self.mean, self.std

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.mean is None or self.std is None:
            raise ValueError("Pipeline has not been trained yet.")
        X_scaled = FeaturePreprocessor.scale_vector(X, self.mean, self.std)
        return self.model.predict(X_scaled)
