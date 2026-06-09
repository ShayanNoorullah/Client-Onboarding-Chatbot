import copy
from typing import Any

from app.agent.state import default_state


class SessionStore:
    """In-memory session state store."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def get(self, session_id: str) -> dict[str, Any]:
        if session_id not in self._sessions:
            state = default_state()
            state["session_id"] = session_id
            self._sessions[session_id] = state
        return self._sessions[session_id]

    def update(self, session_id: str, state: dict[str, Any]) -> None:
        self._sessions[session_id] = copy.deepcopy(state)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def exists(self, session_id: str) -> bool:
        return session_id in self._sessions


session_store = SessionStore()
