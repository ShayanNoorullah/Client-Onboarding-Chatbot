from app.models.user_memory import UserMemory
from app.services.pattern_quality_service import get_learned_constraints


async def build_learned_constraints_text(user_id: str | None, tenant_id: str = "default") -> str:
    lines: list[str] = []
    patterns = await get_learned_constraints(tenant_id)
    lines.extend(patterns[:3])

    if user_id:
        mem = await UserMemory.find_one(UserMemory.user_id == user_id)
        if mem:
            for fact in mem.facts[-5:]:
                if fact.startswith("[correction]"):
                    lines.append(fact.replace("[correction]", "").strip())

    if not lines:
        return "None yet"
    return "\n".join(f"- {line}" for line in lines[:8])
