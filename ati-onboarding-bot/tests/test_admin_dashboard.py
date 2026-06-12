from app.api import admin_routes
from app.api.admin_routes import _avg_turns_to_brief
from app.services.agent_metrics import AgentMetrics


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
