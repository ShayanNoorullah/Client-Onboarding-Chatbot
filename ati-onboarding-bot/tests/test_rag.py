import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.rag.embedder import embed_documents
from app.rag.retriever import query_rag


@pytest.fixture
def kb_files(tmp_path):
    kb_dir = tmp_path / "ati_kb"
    kb_dir.mkdir()
    (kb_dir / "privacy_policy.txt").write_text(
        "ATI does not sell personal information to third parties.",
        encoding="utf-8",
    )
    (kb_dir / "service_catalogue.txt").write_text(
        "Mortgage Website Development Services provide responsive design.",
        encoding="utf-8",
    )
    return kb_dir


@pytest.fixture
def mock_embeddings():
    with patch("app.rag.embedder.get_embeddings") as mock_get:
        instance = MagicMock()
        instance.embed_documents.return_value = [[0.1] * 768]
        instance.embed_query.return_value = [0.1] * 768
        mock_get.return_value = instance
        yield instance


def test_embed_documents_creates_store(kb_files, mock_embeddings, tmp_path):
    vectors_dir = tmp_path / "vectors"

    with patch("app.rag.embedder.Chroma") as mock_chroma:
        mock_chroma.from_documents.return_value = MagicMock()
        embed_documents(
            [str(kb_files / "privacy_policy.txt"), str(kb_files / "service_catalogue.txt")],
            collection="test_kb",
            persist_dir=str(vectors_dir),
        )
        mock_chroma.from_documents.assert_called_once()


def test_query_rag_empty_dir(tmp_path):
    result = query_rag("mortgage website", tmp_path / "nonexistent", "ati_kb")
    assert result == ""


def test_query_rag_mobile_app_content(kb_files, mock_embeddings, tmp_path):
    catalogue = kb_files / "service_catalogue.txt"
    catalogue.write_text(
        "=== MOBILE APP DEVELOPMENT ===\n"
        "ATI builds native and cross-platform mobile applications for iOS and Android.\n"
        "Features include push notifications, offline mode, and app store deployment.",
        encoding="utf-8",
    )
    vectors_dir = tmp_path / "vectors"
    vectors_dir.mkdir()

    mobile_doc = MagicMock()
    mobile_doc.page_content = "ATI builds native and cross-platform mobile applications for iOS and Android."

    mortgage_doc = MagicMock()
    mortgage_doc.page_content = "Mortgage loan application form integration for lending websites."

    with patch("app.rag.retriever.Chroma") as mock_chroma:
        mock_vs = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [mobile_doc]
        mock_vs.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vs

        from app.agent.task_router import build_rag_query

        query = build_rag_query("Mobile App", "mobile_app_development")
        result = query_rag(query, vectors_dir, "ati_kb")
        assert "mobile" in result.lower()
        assert "iOS" in result or "Android" in result


def test_query_rag_with_mock(kb_files, mock_embeddings, tmp_path):
    vectors_dir = tmp_path / "vectors"
    vectors_dir.mkdir()

    mock_doc = MagicMock()
    mock_doc.page_content = "Mortgage Website Development Services"

    with patch("app.rag.retriever.Chroma") as mock_chroma:
        mock_vs = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [mock_doc]
        mock_vs.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vs

        result = query_rag("mortgage website development", vectors_dir, "ati_kb")
        assert "Mortgage Website Development" in result
