import logging
import threading
from pathlib import Path

from langchain_chroma import Chroma

from app.config import settings
from app.llm.factory import get_embeddings

logger = logging.getLogger(__name__)

_chroma_cache: dict[tuple[str, str], object] = {}
_chroma_lock = threading.Lock()


def _query_chroma(question: str, persist_dir: str, collection: str) -> list:
    key = (persist_dir, collection)
    with _chroma_lock:
        if key not in _chroma_cache:
            embeddings = get_embeddings()
            vs = Chroma(
                collection_name=collection,
                embedding_function=embeddings,
                persist_directory=persist_dir,
            )
            _chroma_cache[key] = vs.as_retriever(search_kwargs={"k": 5})
        return _chroma_cache[key].invoke(question)


def query_rag(question: str, persist_dir: str | Path, collection: str) -> str:
    """Return top-5 relevant chunks as a single string."""
    persist_path = Path(persist_dir)
    if not persist_path.exists():
        return ""

    try:
        docs = _query_chroma(question, str(persist_path), collection)
        return "\n\n".join(d.page_content for d in docs)
    except Exception:
        logger.exception("RAG query failed for collection=%s", collection)
        return ""


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def query_combined_rag(
    question: str,
    client_name: str | None = None,
    workspace_slug: str | None = None,
    user_id: str | None = None,
) -> str:
    """Query ATI KB, client/project vectors, and user memory with per-source quotas."""
    tasks: list[tuple[str, str, str, int]] = []

    tasks.append((
        "kb",
        str(settings.ati_kb_vectors_dir),
        "ati_kb",
        settings.RAG_KB_CHARS,
    ))

    learned_dir = settings.ati_kb_vectors_dir
    if (learned_dir / "chroma.sqlite3").exists():
        tasks.append((
            "learned",
            str(learned_dir),
            "ati_kb_learned",
            settings.RAG_LEARNED_CHARS,
        ))

    if client_name:
        client_vectors = settings.client_vectors_dir(client_name, workspace_slug)
        collection = f"project_{workspace_slug}" if workspace_slug else f"client_{settings.client_folder(client_name).name}"
        tasks.append(("client", str(client_vectors), collection, settings.RAG_CLIENT_CHARS))

        if user_id:
            memory_vectors = settings.client_folder(client_name) / "_user_memory" / "vectors"
            if memory_vectors.exists():
                tasks.append((
                    "memory",
                    str(memory_vectors),
                    f"user_memory_{user_id[:8]}",
                    settings.RAG_MEMORY_CHARS,
                ))

    parts: dict[str, str] = {}
    for label, persist, collection, quota in tasks:
        try:
            ctx = query_rag(question, persist, collection)
            if ctx:
                parts[label] = _truncate(ctx, quota)
        except Exception:
            logger.exception("RAG task failed for %s", label)

    ordered_labels = ["kb", "learned", "client", "memory"]
    section_titles = {
        "kb": "ATI Knowledge Base",
        "learned": "Learned Patterns",
        "client": "Client Documents",
        "memory": "User Memory",
    }
    segments = []
    for label in ordered_labels:
        if label in parts:
            segments.append(f"[{section_titles[label]}]\n{parts[label]}")

    combined = "\n\n".join(segments)
    if not combined:
        logger.warning("RAG returned empty context for query=%s", question[:80])
    return combined
