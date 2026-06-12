import pytest

from app.services.feedback_service import task_type_for_stage


def test_task_type_for_stage_requirements():
    assert task_type_for_stage("requirements") == "requirements_chat"


def test_task_type_for_stage_summarise():
    assert task_type_for_stage("summarise") == "brief_extraction"


def test_task_type_for_unknown_stage():
    assert task_type_for_stage("unknown") == "requirements_chat"
