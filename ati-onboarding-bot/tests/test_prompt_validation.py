from app.models.learning_models import LearningExample
from app.models.learning_models import PromptVersion
from app.services.prompt_validation_service import _shadow_addresses_failure, _would_regress


def test_shadow_addresses_failure_with_comment():
    shadow = PromptVersion.model_construct(content="Learned constraint: be clearer")
    example = LearningExample.model_construct(
        label="failure",
        comment="be clearer",
    )
    assert _shadow_addresses_failure(shadow.content, example) is True


def test_would_regress_on_huge_prompt():
    example = LearningExample.model_construct(label="success", assistant_output="ok")
    assert _would_regress("x" * 13000, example) is True
