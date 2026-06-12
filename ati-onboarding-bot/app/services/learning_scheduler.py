import asyncio
import logging

from app.services.pattern_quality_service import review_pattern_quality
from app.services.prompt_improvement_service import process_pending_improvements
from app.services.prompt_validation_service import process_pending_validations

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None


async def _learning_loop() -> None:
    while True:
        try:
            await asyncio.sleep(300)
            improved = await process_pending_improvements()
            validated = await process_pending_validations("default")
            deprecated = await review_pattern_quality("default")
            if improved or validated or deprecated:
                logger.info(
                    "Learning loop: improved=%s validated=%s deprecated=%s",
                    improved,
                    validated,
                    deprecated,
                )
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Learning scheduler error")


def start_learning_scheduler() -> None:
    global _task
    if _task and not _task.done():
        return
    _task = asyncio.create_task(_learning_loop())
    logger.info("Learning scheduler started")
