from typing import List, Dict, Any
from backend.app.memory.conversation_memory import ConversationMemory
from backend.app.memory.repository_memory import RepositoryMemory
from backend.app.memory.session_memory import SessionMemory


class MemoryManager:
    """
    Unified public manager interfacing dialog history, repository structures,
    and temporary session states. This is the exclusive public boundary for memory transactions.
    """

    def __init__(self):
        self._conversation = ConversationMemory()
        self._repository = RepositoryMemory()
        self._session = SessionMemory()

    # --- Conversation Memory ---

    def add_message(self, role: str, content: str) -> None:
        """Adds dialogue logs (role: 'user' | 'assistant')."""
        self._conversation.add_message(role, content)

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns active dialog logs."""
        return self._conversation.get_history()

    def clear_conversation(self) -> None:
        """Purges active dialog logs."""
        self._conversation.clear()

    # --- Repository Memory ---

    def set_repository_context(self, snapshot_id: str, metadata: Dict[str, Any]) -> None:
        """Caches metadata context for a repository snapshot."""
        self._repository.set_context(snapshot_id, metadata)

    def get_repository_context(self, snapshot_id: str) -> Dict[str, Any]:
        """Loads cached snapshot metadata context."""
        return self._repository.get_context(snapshot_id)

    # --- Session Memory ---

    def set_session_value(self, key: str, value: Any) -> None:
        """Stores a temporary variable in active request scope."""
        self._session.set(key, value)

    def get_session_value(self, key: str, default: Any = None) -> Any:
        """Loads temporary variable from active request scope."""
        return self._session.get(key, default)

    def clear_session(self) -> None:
        """Clears active session values."""
        self._session.clear()
