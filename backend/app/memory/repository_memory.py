from typing import Dict, Any


class RepositoryMemory:
    """
    Stores cached repository metadata and structural context keyed by snapshot ID.
    """

    def __init__(self):
        self._context: Dict[str, Dict[str, Any]] = {}

    def set_context(self, snapshot_id: str, metadata: Dict[str, Any]) -> None:
        self._context[snapshot_id] = metadata

    def get_context(self, snapshot_id: str) -> Dict[str, Any]:
        return self._context.get(snapshot_id, {})

    def clear(self) -> None:
        self._context.clear()
