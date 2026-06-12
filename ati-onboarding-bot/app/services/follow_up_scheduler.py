import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.models.follow_up_rule import FollowUpRule
from app.models.onboarding_session import OnboardingSessionDoc
from app.models.user import User
from app.services.email_service import send_templated_email
from app.services.system_config_service import get_effective_settings

logger = logging.getLogger(__name__)

_sent_tracker: dict[str, int] = {}


async def _process_idle_sessions(tenant_id: str, rule: FollowUpRule) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=rule.delay_hours)
    sessions = await OnboardingSessionDoc.find(
        OnboardingSessionDoc.tenant_id == tenant_id,
        OnboardingSessionDoc.done == False,
        OnboardingSessionDoc.updated_at <= cutoff,
    ).to_list()

    for session in sessions:
        track_key = f"{session.session_id}:{rule.template_key}"
        sends = _sent_tracker.get(track_key, 0)
        if sends >= rule.max_sends:
            continue

        user = await User.get(session.user_id)
        if not user or not user.email:
            continue

        ok, msg = await send_templated_email(
            tenant_id=tenant_id,
            template_key=rule.template_key,
            to_email=user.email,
            variables={
                "client_name": session.state.get("client_name", "there") if session.state else "there",
                "session_link": f"/chat.html?session={session.session_id}",
                "stage": session.stage,
            },
        )
        if ok:
            _sent_tracker[track_key] = sends + 1
            logger.info("Follow-up sent for session %s: %s", session.session_id, msg)


async def run_follow_up_cycle(tenant_id: str = "default") -> None:
    cfg = await get_effective_settings(tenant_id)
    if not cfg.get("follow_up_enabled", True):
        return

    rules = await FollowUpRule.find(
        FollowUpRule.tenant_id == tenant_id,
        FollowUpRule.is_active == True,
    ).to_list()

    for rule in rules:
        if rule.trigger == "session_idle":
            await _process_idle_sessions(tenant_id, rule)


def start_follow_up_scheduler() -> None:
    async def _loop() -> None:
        while True:
            try:
                await run_follow_up_cycle("default")
            except Exception:
                logger.exception("Follow-up scheduler error")
            await asyncio.sleep(3600)

    asyncio.create_task(_loop())
