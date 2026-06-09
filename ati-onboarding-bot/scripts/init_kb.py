"""One-time script to index ATI knowledge base into ChromaDB."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.llm.factory import check_ollama_health
from app.rag.embedder import embed_documents


def main():
    health = check_ollama_health()
    if not health["ollama_reachable"]:
        print("ERROR: Ollama is not reachable. Start Ollama and run: python scripts/check_ollama.py")
        sys.exit(1)
    if health["missing"]:
        print(f"ERROR: Missing Ollama models: {', '.join(health['missing'])}")
        print("Pull them with: ollama pull nomic-embed-text")
        sys.exit(1)
    docs = [
        settings.ATI_KB_ROOT / "privacy_policy.txt",
        settings.ATI_KB_ROOT / "service_catalogue.txt",
    ]

    for doc in docs:
        if not doc.exists():
            print(f"ERROR: Missing knowledge base file: {doc}")
            sys.exit(1)

    vectors_dir = settings.ati_kb_vectors_dir
    vectors_dir.mkdir(parents=True, exist_ok=True)

    embed_documents(
        [str(d) for d in docs],
        collection="ati_kb",
        persist_dir=str(vectors_dir),
    )
    print("ATI knowledge base indexed successfully.")
    print(f"  Files: {[d.name for d in docs]}")
    print(f"  Vectors stored in: {vectors_dir}")


if __name__ == "__main__":
    main()
