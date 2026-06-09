from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from app.llm.factory import get_embeddings


def embed_documents(
    file_paths: list[str | Path],
    collection: str,
    persist_dir: str | Path,
) -> None:
    """Chunk and embed documents into ChromaDB."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    embeddings = get_embeddings()

    all_chunks = []
    for path in file_paths:
        path = Path(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        chunks = splitter.create_documents(
            [text], metadatas=[{"source": str(path)}]
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        return

    persist_path = Path(persist_dir)
    persist_path.mkdir(parents=True, exist_ok=True)

    Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        collection_name=collection,
        persist_directory=str(persist_path),
    )


def embed_text(
    text: str,
    collection: str,
    persist_dir: str | Path,
    metadata: dict | None = None,
) -> None:
    """Embed a raw text string into ChromaDB."""
    if not text.strip():
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    embeddings = get_embeddings()
    meta = metadata or {}
    chunks = splitter.create_documents([text], metadatas=[meta])

    persist_path = Path(persist_dir)
    persist_path.mkdir(parents=True, exist_ok=True)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection,
        persist_directory=str(persist_path),
    )
