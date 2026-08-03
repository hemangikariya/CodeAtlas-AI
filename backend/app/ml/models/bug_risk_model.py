from sklearn.ensemble import RandomForestClassifier
import numpy as np


class BugRiskModel:
    """
    Random Forest Classification model predicting repository chunk or file bug risk (0: low, 1: high).
    """

    def __init__(self, n_estimators: int = 100, max_depth: int = 8, random_state: int = 42):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Returns prediction probabilities for confidence calculation.
        """
        return self.model.predict_proba(X)

    @property
    def feature_importances_(self) -> np.ndarray:
        return self.model.feature_importances_
