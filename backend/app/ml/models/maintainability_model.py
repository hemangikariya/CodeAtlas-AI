from sklearn.ensemble import RandomForestRegressor
import numpy as np


class MaintainabilityModel:
    """
    Random Forest Regression model predicting repository maintainability index (0 - 100).
    """

    def __init__(self, n_estimators: int = 100, max_depth: int = 8, random_state: int = 42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    @property
    def feature_importances_(self) -> np.ndarray:
        return self.model.feature_importances_
