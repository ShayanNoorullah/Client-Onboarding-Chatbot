from app.agent import prompts as prompt_module
from app.services.prompt_registry import PROMPT_SEEDS


def test_prompt_seeds_include_slm():
    assert "slm" in PROMPT_SEEDS
    assert "{learned_constraints}" in PROMPT_SEEDS["slm"]
    assert PROMPT_SEEDS["slm"] == prompt_module.SLM_SYSTEM_PROMPT


def test_build_slm_prompt_learned_constraints():
    from app.agent.prompts import build_slm_prompt

    out = build_slm_prompt(
        client_name="Acme",
        stage="requirements",
        assets_count=0,
        rag_context="ctx",
        collected_requirements={},
        learned_constraints="- Always confirm audience",
    )
    assert "Always confirm audience" in out
