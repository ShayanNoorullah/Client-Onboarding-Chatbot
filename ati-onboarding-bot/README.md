# ATI Client Onboarding AI Chatbot v3.2

AI-powered client onboarding for **Awesome Technologies Inc.** — login-first, MongoDB-backed, multi-tenant admin platform, Bootstrap UI, and local Ollama SLMs with ChromaDB RAG. No paid LLM API keys required.

## Features

### End-user experience
- **Login / Register** (email + password) and **Google OAuth**
- **ChatGPT-style** Bootstrap chat UI with sidebar session history
- **Six-stage onboarding** — greeting, consent, identity, requirements, clarify, summarise
- **SLM-driven consent** and **intelligent completion detection** (readiness score + missing fields)
- **File uploads** (PDF, DOCX, images, XLSX, TXT) with RAG indexing and vision description
- **Reference URL research** — paste HTTPS links; agent fetches public page text and uses it in requirements (after consent)
- **Downloadable briefs** (`.md` and PDF export support)
- **User preferences** and per-user learning memory
- **Feedback loop** — per-message thumbs, brief ratings, shadow prompt validation (see [SELF_LEARNING.md](SELF_LEARNING.md))

### Admin platform
- **Dashboard** — KPIs, stage funnel (including completed), 7-day activity, Ollama health, agent metrics, auto-refresh
- **Pipeline** — onboarding sessions, briefs, configurable project types
- **Configuration** — AI config (Ollama models per purpose), system config, SMTP, email templates, follow-up timing, **agent learning** dashboard
- **SaaS workspace** — tenant profile, API keys, usage & limits, audit log
- **Settings / RBAC** — application modules, pages, actions, roles with configurable permission matrix, users
- **Reports** — CSV export
- **Collapsible sidebar icon rail** and responsive admin shell (`admin-v2.css`)

### Platform
- **MongoDB Atlas** — users, sessions, briefs, roles, tenants, audit events, config documents
- **Multi-tenant scoping** — `TenantMiddleware`; super-admin tenant switcher
- **Local Ollama** — `qwen2.5:3b`, `nomic-embed-text`, `llava` (configurable per tenant via AI Configuration)
- **ChromaDB + local disk** — KB vectors (`ati_kb/`) and per-client workspaces (`client_data/`)

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) with required models pulled
- MongoDB Atlas cluster (connection string)
- Google OAuth credentials (optional)

## Quick start

```powershell
cd ati-onboarding-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env: MONGODB_URI, JWT_SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD
python scripts/init_kb.py
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

| URL | Purpose |
|-----|---------|
| [http://127.0.0.1:8001/login.html](http://127.0.0.1:8001/login.html) | User login |
| [http://127.0.0.1:8001/admin/dashboard.html](http://127.0.0.1:8001/admin/dashboard.html) | Admin dashboard |
| [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) | OpenAPI docs |

**Full setup guide:** [SETUP.md](SETUP.md) — installation, SMTP, notifications, webhooks, integrations, DocuSeal, portal, RBAC, troubleshooting.

See `Run.txt` for copy-paste commands and `IMPLEMENTATION.md` for architecture reference.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGODB_URI` | Yes | MongoDB Atlas connection string |
| `JWT_SECRET_KEY` | Yes | Secret for JWT httpOnly cookies |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Yes | First admin user seeded on startup |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | No | Google OAuth sign-in |
| `OLLAMA_BASE_URL` | Yes | Default `http://localhost:11434` |
| `OLLAMA_CHAT_MODEL` | Yes | Default `qwen2.5:3b` |
| `OLLAMA_EMBED_MODEL` | Yes | Default `nomic-embed-text` |
| `OLLAMA_VISION_MODEL` | Yes | Default `llava` |
| `ENCRYPTION_KEY` | Yes | Fernet key for conversation log encryption |

Per-tenant AI and system settings can also be managed in the admin UI and override env defaults at runtime.

### SMTP & notifications

Configure in the admin UI (not `.env`). See **[SETUP.md — Section 6 & 7](SETUP.md#6-smtp--office-365)** for the full Office 365 guide, management recipients, and email template verification.

## API overview

| Area | Prefix / endpoints |
|------|-------------------|
| Auth | `POST /api/auth/register`, `/login`, `/logout`, `GET /me`, Google OAuth |
| User | `GET/PUT /api/user/profile`, `/preferences`, `POST/GET /api/user/sessions`, `/briefs` |
| Chat | `WS /ws/chat/{id}`, `POST /upload/{id}`, `POST /surf/{id}` |
| Briefs | `GET /api/briefs`, `/{id}/download`, `/{id}/feedback` |
| Admin | `GET /api/admin/dashboard`, CRUD `/users`, `/sessions`, `/briefs`, `/reports/export` |
| Config | `GET/PUT /api/admin/config/ai`, `/system`, `/smtp`, `/email-templates`, `/follow-up-rules` |
| Settings | `GET/POST/PUT /api/admin/settings/roles`, `/users`, `/modules`, `/pages`, `/actions` |
| Tenants | `GET/PATCH /api/admin/tenants/current`, `/usage`, `/api-keys` (super-admin: list/create tenants) |
| Webhooks | `GET/POST/PUT/DELETE /api/admin/webhooks`, `/deliveries`, `/{id}/test` |
| Notifications | `GET /api/notifications`, `PATCH /{id}/read`, `POST /read-all` |
| Portal | `GET /api/portal/brief/{token}`, `POST /api/auth/magic-link` |
| Signatures | `POST /api/admin/signatures/briefs/{id}/nda` |
| Audit | `GET /api/admin/audit` |
| Health | `GET /health` |

## Admin settings (RBAC)

Roles are defined in **Settings → Role**. Each role stores a nested permission map:

```
{ module_name: { page_name: { action_key: true|false } } }
```

Application actions (view, insert, update, delete, or custom keys) are managed under **Settings → Application Action** and drive the columns shown in the role permission matrix. Super Admin and Admin roles are seeded with `sort_order` so Super Admin appears first.

## Tests

**106 tests** across auth, agent, RAG, admin dashboard, config, settings, webhooks, portal, notifications, and more:

```powershell
pytest tests/ -v
```

## Project layout (high level)

```
ati-onboarding-bot/
├── main.py                 # FastAPI 3.2.0 entry
├── app/
│   ├── api/                # auth, admin, config, settings, tenant, audit routes
│   ├── agent/              # LangGraph onboarding pipeline
│   ├── models/             # Beanie documents (User, Role, Tenant, Brief, …)
│   ├── services/           # brief, email, audit, usage, AI/system config
│   └── storage/            # file_manager, mongo_session_store, encryptor
├── static/                 # Bootstrap UI (login, chat, admin/*.html, js, css)
├── ati_kb/                 # Knowledge base source + ChromaDB vectors
├── client_data/            # Per-client assets, vectors, summaries (runtime)
├── scripts/                # init_kb.py, check_ollama.py, …
└── tests/                  # 98 pytest tests
```

## Notes

- React `frontend/` is **deprecated** — v3 uses `static/` Bootstrap HTML/JS
- Static assets are cache-busted (`?v=3.8.5` on admin JS/CSS); hard-refresh after upgrades
- Re-index KB after editing `ati_kb/*.txt`: `python scripts/init_kb.py`
- Use `--reload` during development so new API routes and templates load without a manual restart

## Documentation

| File | Contents |
|------|----------|
| **[SETUP.md](SETUP.md)** | **Complete setup guide** — install, SMTP, email, webhooks, Slack/Teams, DocuSeal, portal, RBAC, troubleshooting |
| [docs/n8n/README.md](docs/n8n/README.md) | n8n webhook integration — import sample workflow, wire ATI admin |
| `IMPLEMENTATION.md` | Architecture, flowcharts, API protocol, evolution history |
| `Run.txt` | Quick command reference and admin URLs |
| `.env.example` | Environment variable template with generation commands |
