import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("codeatlas.ml")


class FeatureStore:
    """
    Caches computed snapshot features in memory and on disk.
    Prevents duplicate calculations and facilitates offline training loops.
    """

    def __init__(self, cache_dir: str = "backend/data/features"):
        self.cache_dir = cache_dir
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_path(self, snapshot_id: str) -> str:
        return os.path.join(self.cache_dir, f"{snapshot_id}.json")

    def get(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        # Check memory
        if snapshot_id in self._memory_cache:
            return self._memory_cache[snapshot_id]

        # Check disk
        path = self._get_path(snapshot_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    features = json.load(f)
                self._memory_cache[snapshot_id] = features
                return features
            except Exception as e:
                logger.error(f"Error loading features from store for {snapshot_id}: {str(e)}")
        return None

    def set(self, snapshot_id: str, features: Dict[str, Any]) -> None:
        # Save memory
        self._memory_cache[snapshot_id] = features

        # Save disk
        path = self._get_path(snapshot_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(features, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving features to store for {snapshot_id}: {str(e)}")

    def exists(self, snapshot_id: str) -> bool:
        if snapshot_id in self._memory_cache:
            return True
        return os.path.exists(self._get_path(snapshot_id))

    def invalidate(self, snapshot_id: str) -> None:
        if snapshot_id in self._memory_cache:
            del self._memory_cache[snapshot_id]
        path = self._get_path(snapshot_id)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                logger.error(f"Error invalidating feature store for {snapshot_id}: {str(e)}")


# Singleton instance
feature_store = FeatureStore()
