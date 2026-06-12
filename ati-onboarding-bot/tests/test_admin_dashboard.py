from datetime import datetime, timedelta, timezone

from app.api import admin_routes
from app.api.admin_routes import _as_utc, _avg_turns_to_brief
from app.services.agent_metrics import AgentMetrics


def test_as_utc_handles_naive_and_aware():
    naive = datetime(2026, 6, 1, 12, 0)
    aware = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    assert _as_utc(naive) == aware
    assert _as_utc(aware) == aware
    assert _as_utc(None) is None


def test_at_risk_cutoff_accepts_naive_session_updated_at():
    at_risk_cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    naive_old = (datetime.now(timezone.utc) - timedelta(days=5)).replace(tzinfo=None)
    assert _as_utc(naive_old) <= at_risk_cutoff


def test_avg_turns_to_brief_uses_agent_metrics():
    m = AgentMetrics()
    m.total_turns = 40
    m.sessions_completed = 8
    original = admin_routes.metrics
    admin_routes.metrics = m
    try:
        assert _avg_turns_to_brief() == 5.0
    finally:
        admin_routes.metrics = original


def test_avg_turns_to_brief_zero_when_no_completions():
    original = admin_routes.metrics
    admin_routes.metrics = AgentMetrics()
    try:
        assert _avg_turns_to_brief() == 0.0
    finally:
        admin_routes.metrics = original
