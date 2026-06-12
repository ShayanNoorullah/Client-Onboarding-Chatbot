from app.api.settings_routes import _sort_actions
from app.models.app_action import ApplicationAction


def test_sort_actions_pinned_first():
    actions = [
        ApplicationAction.model_construct(page_name="A", action_name="View", action_key="view", is_pinned=False, sort_order=1),
        ApplicationAction.model_construct(page_name="B", action_name="View", action_key="view", is_pinned=True, sort_order=0),
    ]
    sorted_actions = _sort_actions(actions)
    assert sorted_actions[0].page_name == "B"


def test_application_action_has_pin_and_sort_fields():
    action = ApplicationAction.model_construct(
        page_name="Dashboard",
        action_name="View",
        action_key="view",
        sort_order=2,
        is_pinned=True,
    )
    data = action.to_dict()
    assert data["sort_order"] == 2
    assert data["is_pinned"] is True
