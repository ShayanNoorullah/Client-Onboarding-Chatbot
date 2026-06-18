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


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    is_active: bool = True
    permissions: dict[str, dict[str, dict[str, bool]]] = Field(default_factory=dict)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None
    permissions: dict[str, dict[str, dict[str, bool]]] | None = None


class ModuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    icon: str = "fa fa-th-large"
    sort_order: int = 0
    is_active: bool = True


class ModuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class PageCreate(BaseModel):
    module_name: str
    page_name: str
    route: str
    sort_order: int = 0
    is_active: bool = True


class PageUpdate(BaseModel):
    module_name: str | None = None
    page_name: str | None = None
    route: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ActionCreate(BaseModel):
    page_name: str
    action_name: str
    action_key: str
    sort_order: int = 0
    is_pinned: bool = False
    is_active: bool = True


class ActionUpdate(BaseModel):
    page_name: str | None = None
    action_name: str | None = None
    action_key: str | None = None
    sort_order: int | None = None
    is_pinned: bool | None = None
    is_active: bool | None = None


class ActionPatch(BaseModel):
    is_active: bool | None = None
    is_pinned: bool | None = None


class TenantUpdate(BaseModel):
    name: str | None = None
    plan: str | None = None
    status: str | None = None
    custom_domain: str | None = None
    branding: dict[str, str] | None = None
    limits: dict[str, int] | None = None


class SmtpConfigUpdate(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    encryption_protocol: str = "STARTTLS"
    from_email: str
    username: str
    password: str = ""


class SmtpTestRequest(BaseModel):
    test_email: EmailStr


class SurfUrlRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2000)


class SystemConfigUpdate(BaseModel):
    product_name: str | None = None
    support_email: str | None = None
    privacy_url: str | None = None
    phone: str | None = None
    max_upload_size_mb: int | None = None
    max_files_per_session: int | None = None
    surf_enabled: bool | None = None
    max_urls_per_session: int | None = None
    email_notifications_enabled: bool | None = None
    follow_up_enabled: bool | None = None
    notification_to_emails: list[str] | None = None
    notification_cc_emails: list[str] | None = None
    slack_webhook_url: str | None = None
    teams_webhook_url: str | None = None
    docuseal_api_url: str | None = None
    docuseal_api_key: str | None = None
    docuseal_nda_template_id: str | None = None
    default_language: str | None = None


class WebhookSubscriptionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=500)
    secret: str = ""
    event_types: list[str] = Field(default_factory=list)
    max_retries: int = Field(default=3, ge=1, le=10)


class WebhookSubscriptionUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    secret: str | None = None
    event_types: list[str] | None = None
    is_active: bool | None = None
    max_retries: int | None = None


class ModelProfileUpdate(BaseModel):
    id: str | None = None
    name: str
    provider: str = "ollama"
    model_id: str
    purposes: list[str] = Field(default_factory=list)
    temperature: float = 0.3
    max_tokens: int = 512
    is_enabled: bool = True
    is_default: bool = False


class AiConfigUpdate(BaseModel):
    llm_provider: str | None = None
    ollama_base_url: str | None = None
    chat_temperature: float | None = None
    num_predict: int | None = None
    rag_context_max_chars: int | None = None
    rag_kb_chars: int | None = None
    rag_client_chars: int | None = None
    rag_memory_chars: int | None = None
    rag_learned_chars: int | None = None
    prompt_version: str | None = None
    models: list[ModelProfileUpdate] | None = None


class EmailTemplateCreate(BaseModel):
    key: str = Field(min_length=1, max_length=64)
    name: str
    subject: str
    body_html: str = ""
    body_text: str = ""
    variables: list[str] = Field(default_factory=list)
    is_active: bool = True


class EmailTemplateUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    variables: list[str] | None = None
    is_active: bool | None = None


class EmailTemplatePreview(BaseModel):
    variables: dict[str, str] = Field(default_factory=dict)


class FollowUpRuleUpdate(BaseModel):
    id: str | None = Field(default=None)
    trigger: str | None = None
    stage: str | None = None
    delay_hours: int | None = None
    template_key: str | None = None
    is_active: bool | None = None
    max_sends: int | None = None


class FollowUpRulesBulkUpdate(BaseModel):
    rules: list[FollowUpRuleUpdate]


class TenantCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=64)
    name: str
    plan: str = "free"


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class UserCreateAdmin(BaseModel):
    full_name: str = Field(min_length=2)
    email: EmailStr
    username: str | None = None
    password: str = Field(min_length=8)
    role_name: str = "User"
    is_active: bool = True


class UserUpdateAdmin(BaseModel):
    full_name: str | None = None
    username: str | None = None
    role_name: str | None = None
    is_active: bool | None = None


class UserPatchAdmin(BaseModel):
    is_active: bool


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


class FeedbackSubmitRequest(BaseModel):
    feedback_type: str
    signal: int = 0
    comment: str = ""
    session_id: str | None = None
    turn_id: str | None = None
    brief_id: str | None = None
    task_type: str = ""
    stage: str = ""
    rating: int | None = None
    context: dict | None = None
