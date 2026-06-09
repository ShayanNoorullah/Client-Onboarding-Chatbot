import logging

from app.llm.factory import describe_image_ollama

logger = logging.getLogger(__name__)


def describe_image(image_path: str) -> str:
    """Send image to Ollama vision model and return a detailed description."""
    try:
        return describe_image_ollama(image_path)
    except Exception as e:
        logger.exception("Ollama vision failed for %s", image_path)
        return (
            f"Image uploaded ({image_path.split('/')[-1]}). "
            f"Automatic description unavailable: {e}. "
            "Please describe the image in chat."
        )
