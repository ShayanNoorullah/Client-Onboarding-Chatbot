import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from app.agent.state import default_state
from app.models.onboarding_session import OnboardingSessionDoc


class MongoSessionStore:
    """MongoDB-backed session store with in-memory cache."""

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    async def create(self, user_id: str, full_name: str | None = None) -> dict[str, Any]:
        from app.storage.file_manager import sanitise_name

        session_id = str(uuid.uuid4())
        state = default_state()
        state["session_id"] = session_id
        state["user_id"] = user_id
        if full_name:
            state["client_name"] = sanitise_name(full_name)
        doc = OnboardingSessionDoc(
            user_id=user_id,
            session_id=session_id,
            stage=state["stage"],
            state=state,
        )
        await doc.insert()
        self._cache[session_id] = copy.deepcopy(state)
        return state

    async def get(self, session_id: str, user_id: str | None = None) -> dict[str, Any]:
        if session_id in self._cache:
            return copy.deepcopy(self._cache[session_id])

        doc = await OnboardingSessionDoc.find_one(OnboardingSessionDoc.session_id == session_id)
        if not doc:
            raise KeyError(f"Session not found: {session_id}")
        if user_id and doc.user_id != user_id:
            raise PermissionError("Session does not belong to user")
        state = copy.deepcopy(doc.state)
        state["session_id"] = session_id
        self._cache[session_id] = copy.deepcopy(state)
        return state

    def get_sync(self, session_id: str) -> dict[str, Any]:
        """Sync read from cache only (for thread pool agent)."""
        if session_id not in self._cache:
            raise KeyError(f"Session not in cache: {session_id}")
        return copy.deepcopy(self._cache[session_id])

    async def update(self, session_id: str, state: dict[str, Any]) -> None:
        self._cache[session_id] = copy.deepcopy(state)
        doc = await OnboardingSessionDoc.find_one(OnboardingSessionDoc.session_id == session_id)
        if doc:
            doc.stage = state.get("stage", doc.stage)
            doc.state = state
            doc.consent_given = state.get("consent_given", False)
            doc.done = state.get("done", False)
            doc.ref_id = state.get("ref_id")
            collected = state.get("collected_requirements", {})
            doc.project_type = collected.get("project_type")
            doc.updated_at = datetime.now(timezone.utc)
            await doc.save()

    def update_sync(self, session_id: str, state: dict[str, Any]) -> None:
        """Sync cache update (Mongo persist happens via async wrapper)."""
        self._cache[session_id] = copy.deepcopy(state)

    async def delete(self, session_id: str) -> None:
        self._cache.pop(session_id, None)
        doc = await OnboardingSessionDoc.find_one(OnboardingSessionDoc.session_id == session_id)
        if doc:
            await doc.delete()

    async def list_for_user(self, user_id: str) -> list[dict]:
        docs = await OnboardingSessionDoc.find(
            OnboardingSessionDoc.user_id == user_id
        ).sort(-OnboardingSessionDoc.updated_at).to_list()
        return [d.to_summary() for d in docs]


mongo_session_store = MongoSessionStore()
