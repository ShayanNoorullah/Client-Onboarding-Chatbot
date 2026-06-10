from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=8)


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: str = "user"


class AdminUserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8)


class SessionUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=80)
    pinned: bool | None = None


class UserPreferencesUpdate(BaseModel):
    ati_theme: str | None = None
    ati_theme_preset: str | None = None
    ati_custom_theme: str | None = None
    ati_chat_density: str | None = None
    ati_chat_width: str | None = None
    ati_chat_style: str | None = None
    ati_chat_user_bubble: str | None = None
    ati_chat_assistant_bubble: str | None = None
    ati_chat_accent: str | None = None
    ati_send_on_enter: str | None = None
    ati_show_chips: str | None = None
    ati_show_typing: str | None = None
    ati_auto_scroll: str | None = None
    ati_reduce_motion: str | None = None
    ati_ui_animations: str | None = None
