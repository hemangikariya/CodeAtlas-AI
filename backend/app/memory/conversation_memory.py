from typing import List, Dict, Any


class ConversationMemory:
    """
    Stores and manages dialog history between user and agent.
    """

    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str) -> None:
        self._history.append({
            "role": role,
            "content": content
        })

    def get_history(self) -> List[Dict[str, Any]]:
        return self._history

    def clear(self) -> None:
        self._history.clear()
