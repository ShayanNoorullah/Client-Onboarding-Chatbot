# ATI Client Onboarding AI Chatbot v3

AI-powered onboarding for Awesome Technologies Inc. — login-first, MongoDB-backed, Bootstrap UI, local Ollama SLMs + ChromaDB RAG.

## v3 Features

- **Login / Register** (email + password) and **Google OAuth**
- **MongoDB Atlas** for users, sessions, briefs
- **Bootstrap HTML/JS** chat UI (ChatGPT-style sidebar layout)
- **Admin dashboard** with KPIs and user/session/brief CRUD
- **SLM-driven consent** and **intelligent completion detection**
- **Downloadable briefs** (`.md`) for users and admins
- Local Ollama (`qwen2.5:3b`, `nomic-embed-text`, `llava`) — no API keys

## Prerequisites

- Python 3.11+
- Ollama with models pulled
- MongoDB Atlas cluster (connection string)
- Google OAuth credentials (optional, for Google sign-in)

## Setup

```powershell
cd ati-onboarding-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env: MONGODB_URI, JWT_SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD
python scripts/init_kb.py
uvicorn main:app --host 127.0.0.1 --port 8001
```

Open [http://127.0.0.1:8001/login.html](http://127.0.0.1:8001/login.html)

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGODB_URI` | Yes | MongoDB Atlas connection string |
| `JWT_SECRET_KEY` | Yes | Secret for JWT cookies |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Yes | First admin seeded on startup |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | No | Google OAuth |
| `OLLAMA_*` | Yes | Ollama models (see v2 docs) |

## API overview

| Area | Endpoints |
|------|-----------|
| Auth | `POST /api/auth/register`, `/login`, `GET /google/login`, `/me` |
| User | `POST /api/user/sessions`, `GET /profile`, `/sessions`, `/briefs` |
| Chat | `WS /ws/chat/{id}`, `POST /upload/{id}` |
| Briefs | `GET /api/briefs/{id}/download` |
| Admin | `GET /api/admin/dashboard`, CRUD `/users`, `/sessions`, `/briefs` |

## Tests

```powershell
pytest tests/ -v
```

## Notes

- React `frontend/` is **deprecated** — v3 uses `static/` Bootstrap UI
- ChromaDB vectors and uploaded files remain on local disk (`client_data/`)
- Re-index KB after editing `ati_kb/*.txt`
