"""User UI preference defaults and validation."""

from typing import Any

ALLOWED_PREFERENCE_KEYS = frozenset({
    "ati_theme",
    "ati_theme_preset",
    "ati_custom_theme",
    "ati_chat_density",
    "ati_chat_width",
    "ati_chat_style",
    "ati_chat_user_bubble",
    "ati_chat_assistant_bubble",
    "ati_chat_accent",
    "ati_send_on_enter",
    "ati_show_chips",
    "ati_show_typing",
    "ati_auto_scroll",
    "ati_reduce_motion",
    "ati_ui_animations",
})

DEFAULT_PREFERENCES: dict[str, str] = {
    "ati_theme": "system",
    "ati_theme_preset": "default",
    "ati_custom_theme": "{}",
    "ati_chat_density": "comfortable",
    "ati_chat_width": "wide",
    "ati_chat_style": "default",
    "ati_chat_user_bubble": "",
    "ati_chat_assistant_bubble": "",
    "ati_chat_accent": "",
    "ati_send_on_enter": "true",
    "ati_show_chips": "true",
    "ati_show_typing": "true",
    "ati_auto_scroll": "true",
    "ati_reduce_motion": "false",
    "ati_ui_animations": "true",
}

_VALIDATORS: dict[str, set[str]] = {
    "ati_theme": {"system", "light", "dark"},
    "ati_theme_preset": {
        "default", "ocean", "forest", "sunset", "violet", "slate", "high-contrast", "custom",
    },
    "ati_chat_density": {"comfortable", "compact"},
    "ati_chat_width": {"narrow", "standard", "wide", "full"},
    "ati_chat_style": {"default", "soft", "contrast", "minimal"},
    "ati_send_on_enter": {"true", "false"},
    "ati_show_chips": {"true", "false"},
    "ati_show_typing": {"true", "false"},
    "ati_auto_scroll": {"true", "false"},
    "ati_reduce_motion": {"true", "false"},
    "ati_ui_animations": {"true", "false"},
}


def _is_hex_color(value: str) -> bool:
    v = value.strip()
    if len(v) == 7 and v.startswith("#"):
        try:
            int(v[1:], 16)
            return True
        except ValueError:
            return False
    return False


def validate_preference_value(key: str, value: Any) -> str | None:
    """Return normalized string value or None if invalid."""
    if key not in ALLOWED_PREFERENCE_KEYS:
        return None
    if value is None:
        return None
    s = str(value).strip()
    if key in _VALIDATORS:
        return s if s in _VALIDATORS[key] else None
    if key == "ati_custom_theme":
        if s in ("", "{}"):
            return "{}"
        import json

        try:
            data = json.loads(s) if isinstance(value, str) else value
            if not isinstance(data, dict):
                return None
            for k in ("primary", "surface", "text", "accent", "border"):
                if k in data and data[k] and not _is_hex_color(str(data[k])):
                    return None
            return json.dumps({k: data[k] for k in data if k in ("primary", "surface", "text", "accent", "border")})
        except (json.JSONDecodeError, TypeError):
            return None
    if key in ("ati_chat_user_bubble", "ati_chat_assistant_bubble", "ati_chat_accent"):
        if s == "":
            return ""
        return s if _is_hex_color(s) else None
    return s


def merge_preferences(stored: dict[str, Any] | None) -> dict[str, str]:
    merged = dict(DEFAULT_PREFERENCES)
    if stored:
        for key, value in stored.items():
            normalized = validate_preference_value(key, value)
            if normalized is not None:
                merged[key] = normalized
    return merged


def apply_preference_updates(
    current: dict[str, Any] | None,
    updates: dict[str, Any],
) -> dict[str, str]:
    merged = merge_preferences(current)
    for key, value in updates.items():
        if key not in ALLOWED_PREFERENCE_KEYS:
            continue
        normalized = validate_preference_value(key, value)
        if normalized is not None:
            merged[key] = normalized
    return merged
