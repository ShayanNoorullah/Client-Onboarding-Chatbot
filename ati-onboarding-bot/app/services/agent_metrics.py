"""In-process agent timing and funnel metrics."""

import logging
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_MAX_SAMPLES = 200


@dataclass
class AgentMetrics:
    turn_latencies_ms: deque = field(default_factory=lambda: deque(maxlen=_MAX_SAMPLES))
    rag_latencies_ms: deque = field(default_factory=lambda: deque(maxlen=_MAX_SAMPLES))
    llm_latencies_ms: deque = field(default_factory=lambda: deque(maxlen=_MAX_SAMPLES))
    fallback_count: int = 0
    turns_by_stage: dict[str, int] = field(default_factory=dict)
    sessions_completed: int = 0
    total_turns: int = 0

    def record_turn(self, stage: str, total_ms: float, *, used_fallback: bool = False) -> None:
        self.turn_latencies_ms.append(total_ms)
        self.total_turns += 1
        self.turns_by_stage[stage] = self.turns_by_stage.get(stage, 0) + 1
        if used_fallback:
            self.fallback_count += 1

    def record_rag(self, ms: float) -> None:
        self.rag_latencies_ms.append(ms)

    def record_llm(self, ms: float) -> None:
        self.llm_latencies_ms.append(ms)

    def record_completion(self) -> None:
        self.sessions_completed += 1

    def _percentile(self, samples: deque, pct: float) -> float:
        if not samples:
            return 0.0
        ordered = sorted(samples)
        idx = int(len(ordered) * pct / 100)
        idx = min(idx, len(ordered) - 1)
        return round(ordered[idx], 1)

    def summary(self) -> dict[str, Any]:
        return {
            "total_turns": self.total_turns,
            "sessions_completed": self.sessions_completed,
            "fallback_count": self.fallback_count,
            "fallback_rate_pct": round(
                (self.fallback_count / self.total_turns * 100) if self.total_turns else 0, 1
            ),
            "turn_latency_p50_ms": self._percentile(self.turn_latencies_ms, 50),
            "turn_latency_p95_ms": self._percentile(self.turn_latencies_ms, 95),
            "rag_latency_p50_ms": self._percentile(self.rag_latencies_ms, 50),
            "llm_latency_p50_ms": self._percentile(self.llm_latencies_ms, 50),
            "turns_by_stage": dict(self.turns_by_stage),
        }


metrics = AgentMetrics()


@contextmanager
def timed(section: str, session_id: str = "", stage: str = ""):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        if section == "rag":
            metrics.record_rag(elapsed_ms)
        elif section == "llm":
            metrics.record_llm(elapsed_ms)
        logger.info(
            "agent_timing section=%s session=%s stage=%s ms=%.1f",
            section,
            session_id[:8] if session_id else "-",
            stage or "-",
            elapsed_ms,
        )
