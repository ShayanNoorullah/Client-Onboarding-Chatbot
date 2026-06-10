from datetime import datetime, timezone


def display_name_for_session(
    *,
    title: str | None = None,
    project_type: str | None = None,
    stage: str | None = None,
) -> str:
    if title and title.strip():
        return title.strip()
    if project_type:
        return project_type.replace("_", " ")
    if stage and stage not in ("greeting", "consent"):
        return stage.replace("_", " ").title()
    return "New chat"


def session_matches_query(doc, q: str) -> bool:
    needle = q.strip().lower()
    if not needle:
        return True
    haystacks = [
        getattr(doc, "title", None) or "",
        getattr(doc, "project_type", None) or "",
        getattr(doc, "ref_id", None) or "",
        getattr(doc, "stage", None) or "",
        getattr(doc, "session_id", None) or "",
        getattr(doc, "user_id", None) or "",
        display_name_for_session(
            title=getattr(doc, "title", None),
            project_type=getattr(doc, "project_type", None),
            stage=getattr(doc, "stage", None),
        ),
    ]
    return any(needle in h.lower() for h in haystacks)


def sort_sessions(docs: list) -> list:
    def sort_key(doc) -> tuple:
        pinned = bool(getattr(doc, "pinned", False))
        pinned_rank = 0 if pinned else 1
        pinned_ts = getattr(doc, "pinned_at", None) or datetime.min.replace(tzinfo=timezone.utc)
        updated = getattr(doc, "updated_at", None) or datetime.min.replace(tzinfo=timezone.utc)
        return (pinned_rank, -pinned_ts.timestamp(), -updated.timestamp())

    return sorted(docs, key=sort_key)
