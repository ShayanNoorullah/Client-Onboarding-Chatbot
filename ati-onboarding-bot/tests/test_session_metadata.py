from datetime import datetime, timezone
from types import SimpleNamespace

from app.storage.session_display import (
    display_name_for_session,
    session_matches_query,
    sort_sessions,
)


def test_display_name_prefers_title():
    assert display_name_for_session(title="My Website Chat") == "My Website Chat"


def test_display_name_falls_back_to_project_type():
    assert display_name_for_session(project_type="mobile_app_development") == "mobile app development"


def test_display_name_default_new_chat():
    assert display_name_for_session() == "New chat"


def test_session_matches_query_by_title():
    doc = SimpleNamespace(
        title="Mortgage Portal",
        project_type="website_development",
        ref_id=None,
        stage="requirements",
        session_id="s1",
        user_id="u1",
    )
    assert session_matches_query(doc, "mortgage") is True
    assert session_matches_query(doc, "nomatch") is False


def test_session_matches_query_by_project_type():
    doc = SimpleNamespace(
        title=None,
        project_type="mobile_app_development",
        ref_id=None,
        stage="requirements",
        session_id="s1",
        user_id="u1",
    )
    assert session_matches_query(doc, "mobile") is True


def test_sort_sessions_pinned_first():
    base = datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc)
    pinned = SimpleNamespace(
        session_id="pinned",
        pinned=True,
        pinned_at=base,
        updated_at=base,
    )
    older = SimpleNamespace(
        session_id="older",
        pinned=False,
        pinned_at=None,
        updated_at=base,
    )
    newer = SimpleNamespace(
        session_id="newer",
        pinned=False,
        pinned_at=None,
        updated_at=datetime(2026, 6, 9, 12, 0, tzinfo=timezone.utc),
    )
    sorted_docs = sort_sessions([older, newer, pinned])
    assert [d.session_id for d in sorted_docs] == ["pinned", "newer", "older"]
