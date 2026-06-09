from pathlib import Path

from langchain_community.vectorstores import Chroma

from app.config import settings
from app.llm.factory import get_embeddings


def get_retriever(persist_dir: str | Path, collection: str):
    embeddings = get_embeddings()
    vs = Chroma(
        collection_name=collection,
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )
    return vs.as_retriever(search_kwargs={"k": 5})


def query_rag(question: str, persist_dir: str | Path, collection: str) -> str:
    """Return top-5 relevant chunks as a single string."""
    persist_path = Path(persist_dir)
    if not persist_path.exists():
        return ""

    try:
        retriever = get_retriever(persist_path, collection)
        docs = retriever.invoke(question)
        return "\n\n".join(d.page_content for d in docs)
    except Exception:
        return ""


def query_combined_rag(question: str, client_name: str | None = None) -> str:
    """Query ATI KB and optionally client-specific vectors."""
    parts = []

    kb_context = query_rag(
        question,
        settings.ati_kb_vectors_dir,
        "ati_kb",
    )
    if kb_context:
        parts.append(f"[ATI Knowledge Base]\n{kb_context}")

    if client_name:
        client_vectors = settings.client_vectors_dir(client_name)
        client_context = query_rag(
            question,
            client_vectors,
            f"client_{settings.client_folder(client_name).name}",
        )
        if client_context:
            parts.append(f"[Client Documents]\n{client_context}")

    combined = "\n\n".join(parts)
    max_chars = settings.RAG_CONTEXT_MAX_CHARS
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n...[truncated]"
    return combined
