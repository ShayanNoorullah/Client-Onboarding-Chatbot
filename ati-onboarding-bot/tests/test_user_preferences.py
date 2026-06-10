from app.services.user_preferences import (
    DEFAULT_PREFERENCES,
    apply_preference_updates,
    merge_preferences,
    validate_preference_value,
)


def test_merge_preferences_uses_defaults():
    merged = merge_preferences(None)
    assert merged == DEFAULT_PREFERENCES


def test_merge_preferences_stores_valid_values():
    merged = merge_preferences({"ati_theme": "dark", "ati_chat_width": "full"})
    assert merged["ati_theme"] == "dark"
    assert merged["ati_chat_width"] == "full"


def test_validate_rejects_invalid_theme():
    assert validate_preference_value("ati_theme", "neon") is None


def test_validate_custom_theme_json():
    value = validate_preference_value(
        "ati_custom_theme",
        '{"primary":"#112233","surface":"#FFFFFF"}',
    )
    assert value is not None
    assert "#112233" in value


def test_apply_preference_updates_partial():
    result = apply_preference_updates(
        {"ati_theme": "light"},
        {"ati_theme": "dark", "ati_theme_preset": "ocean", "ati_chat_width": "invalid"},
    )
    assert result["ati_theme"] == "dark"
    assert result["ati_theme_preset"] == "ocean"
    assert result["ati_chat_width"] == "wide"
