"""Re-index learned patterns into ATI knowledge base vectors."""
import logging
from app.config import settings
from app.rag.embedder import embed_documents
logger = logging.getLogger(__name__)

def reindex_learned_patterns() -> bool:
    patterns_file = settings.ATI_KB_ROOT / "learned_patterns.txt"
    if not patterns_file.exists() or patterns_file.stat().st_size == 0:
        return False
    try:
        vectors_dir = settings.ati_kb_vectors_dir
        vectors_dir.mkdir(parents=True, exist_ok=True)
        embed_documents([str(patterns_file)], collection="ati_kb_learned", persist_dir=str(vectors_dir))
        logger.info("Re-indexed learned patterns into ati_kb_learned")
        return True
    except Exception:
        logger.exception("Failed to re-index learned patterns")
        return False
