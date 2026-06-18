# ATI Client Onboarding Agent — Setup Guide

Complete setup reference for local development and production configuration. For architecture details see [IMPLEMENTATION.md](IMPLEMENTATION.md). For daily commands see [Run.txt](Run.txt).

---

## Table of contents

1. [First-time installation](#1-first-time-installation)
2. [Environment variables & secrets](#2-environment-variables--secrets)
3. [Ollama & knowledge base](#3-ollama--knowledge-base)
4. [MongoDB Atlas](#4-mongodb-atlas)
5. [Google OAuth (optional)](#5-google-oauth-optional)
6. [SMTP — Office 365](#6-smtp--office-365)
7. [Email notifications](#7-email-notifications)
8. [Webhooks & CRM integrations](#8-webhooks--crm-integrations)
9. [Slack & Microsoft Teams](#9-slack--microsoft-teams)
10. [DocuSeal e-signature (optional)](#10-docuseal-e-signature-optional)
11. [Client portal & magic links](#11-client-portal--magic-links)
12. [Admin RBAC & roles](#12-admin-rbac--roles)
13. [Verification checklist](#13-verification-checklist)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. First-time installation

### Prerequisites

| Requirement | Version / notes |
|-------------|---------------|
| Python | 3.11+ |
| Ollama | Latest — [ollama.com](https://ollama.com/) |
| MongoDB | Atlas cluster (or local MongoDB 6+) |
| Git | For cloning the repo |

### Steps (Windows PowerShell)

```powershell
cd ati-onboarding-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env — see Section 2
python scripts/init_kb.py
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

### URLs after startup

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8001/login.html | User login / register |
| http://127.0.0.1:8001/admin/dashboard.html | Admin dashboard |
| http://127.0.0.1:8001/docs | OpenAPI (Swagger) docs |
| http://127.0.0.1:8001/health | Health + Ollama status |

On first startup the app seeds: default tenant, admin user, roles, email templates, SMTP config shell, and RBAC pages.

**Default admin** comes from `.env`: `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

---

## 2. Environment variables & secrets

Copy `.env.example` to `.env` and fill in every **Required** row.

### Required variables

| Variable | How to obtain |
|----------|---------------|
| `MONGODB_URI` | MongoDB Atlas → Connect → Drivers → connection string |
| `MONGODB_DB_NAME` | Database name (default `ati_onboarding`) |
| `JWT_SECRET_KEY` | Long random string (32+ chars). Example: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ENCRYPTION_KEY` | Fernet key for SMTP password + sensitive config encryption. Generate once: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `ADMIN_EMAIL` | First admin login email |
| `ADMIN_PASSWORD` | First admin login password (change after first login) |

### Ollama (defaults usually fine)

| Variable | Default |
|----------|---------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `OLLAMA_CHAT_MODEL` | `qwen2.5:3b` |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` |
| `OLLAMA_VISION_MODEL` | `llava` |

### Security rules

- **Never** commit `.env`, SMTP passwords, or API keys to git.
- SMTP credentials are stored **encrypted** in MongoDB (`smtp_config` collection) via `ENCRYPTION_KEY`.
- Rotate any password that was ever pasted into `Run.txt` or chat logs.

---

## 3. Ollama & knowledge base

### Install models

```powershell
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
ollama pull llava
```

Verify:

```powershell
python scripts/check_ollama.py
# or
curl http://localhost:11434/api/tags
```

### Index the ATI knowledge base

Required before chat RAG works:

```powershell
python scripts/init_kb.py
```

Re-index after editing `ati_kb/*.txt`:

```powershell
Remove-Item -Recurse -Force ati_kb\vectors
python scripts/init_kb.py
```

### Admin AI configuration (optional override)

Admin → **Configuration → AI Configuration** (`/admin/config-ai.html`)

- Set Ollama base URL and per-purpose models (chat, embed, vision).
- Use **Test Ollama** to verify connectivity from the server.

---

## 4. MongoDB Atlas

1. Create a free or paid cluster at [cloud.mongodb.com](https://cloud.mongodb.com).
2. Database Access → create a user with read/write on your database.
3. Network Access → add your IP (or `0.0.0.0/0` for dev only).
4. Connect → Drivers → copy connection string into `MONGODB_URI`.
5. Set `MONGODB_DB_NAME=ati_onboarding` (or your chosen name).

On startup, Beanie initializes collections and `seeders.py` runs migrations (roles, pages, templates).

---

## 5. Google OAuth (optional)

1. [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials.
2. Create **OAuth 2.0 Client ID** (Web application).
3. Authorized redirect URI: `http://127.0.0.1:8001/api/auth/google/callback`
4. Set in `.env`:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8001/api/auth/google/callback
FRONTEND_URL=http://127.0.0.1:8001
```

5. Restart uvicorn. **Sign in with Google** appears on login/register pages.

---

## 6. SMTP — Office 365

Email is configured in the **admin UI** (not `.env`). SMTP passwords are encrypted in MongoDB.

### Step A — Microsoft 365 (IT admin)

1. Use a **licensed mailbox** (e.g. `donotreply1@awesometechinc.com`) allowed to send externally.
2. [Microsoft 365 Admin](https://admin.microsoft.com) → **Users** → **Active users** → select mailbox.
3. **Mail** tab → **Manage email apps** → enable **Authenticated SMTP**.
4. Ensure outbound **port 587** is open from the machine running uvicorn.
5. If MFA blocks basic auth, use one of:
   - **SMTP relay** via Exchange Online connector (port 25, IP-based) — [Microsoft Learn](https://learn.microsoft.com/en-us/exchange/mail-flow-best-practices/how-to-set-up-a-multifunction-device-or-application-to-send-email-using-microsoft-365-or-office-365)
   - OAuth 2.0 SMTP (not yet in app — contact IT for relay setup)

### Step B — Application

1. Confirm `ENCRYPTION_KEY` is set in `.env` (required to store SMTP password).
2. Log in as admin → **Configuration → SMTP**:  
   http://127.0.0.1:8001/admin/config-smtp.html

### Step C — SMTP form values

| Field | Value |
|-------|-------|
| SMTP Host | `smtp.office365.com` |
| SMTP Port | `587` |
| Encryption Protocol | **STARTTLS** (not SSL/465) |
| From Email | `donotreply1@awesometechinc.com` |
| Username | Same as From Email (full address) |
| Password | Mailbox password (stored encrypted) |

Click **Save Configuration**.

### Step D — Test connection

1. Click **Test Connection** on the SMTP page.
2. Enter your email → **Send Test**.
3. Success: you receive an email with subject **"SMTP Test"**.
4. Common failures:

| Error | Fix |
|-------|-----|
| `535 Authentication unsuccessful` | Enable Authenticated SMTP; verify username/password |
| Connection timeout | Open port 587; check firewall |
| `SmtpClientAuthentication is disabled` | Tenant blocks SMTP AUTH — use relay or OAuth |

---

## 7. Email notifications

### Enable notifications

Admin → **Configuration → System Configuration**:  
http://127.0.0.1:8001/admin/config-system.html

| Setting | Recommended |
|---------|-------------|
| Email notifications | ON |
| Follow-up emails | ON (optional) |
| Management To | `hassan.khan@awesometechinc.com` (comma-separated) |
| Management CC | Optional CC addresses |
| Default language | `en` or `es` |

### Email templates

Admin → **Configuration → Email Templates**:  
http://127.0.0.1:8001/admin/config-email-templates.html

Seeded templates (verify they exist):

| Template key | When sent | Recipient |
|--------------|-----------|-----------|
| `welcome` | User registers | Client |
| `brief_ready` | Brief completed | Client |
| `brief_submitted_admin` | Brief completed | Management (To/CC from System Config) |
| `session_reminder` | Idle session (follow-up scheduler) | Client |
| `session_abandoned` | Abandoned session rule | Client |
| `session_magic_link` | Magic link requested | Client |

Templates support variables like `{{client_name}}`, `{{brief_link}}`, `{{ref_id}}`.

### Follow-up timing (optional)

Admin → **Configuration → Follow-up Timing**:  
http://127.0.0.1:8001/admin/config-followup.html

Default: reminder after 24 hours idle, max 3 sends, template `session_reminder`.

### End-to-end email test

1. Configure SMTP (Section 6) and management recipients (above).
2. Register a new user → should receive `welcome` email.
3. Complete an onboarding session to brief → client gets `brief_ready`; management gets `brief_submitted_admin`.

---

## 8. Webhooks & CRM integrations

Receive `brief.created`, `user.registered`, `session.created`, etc. in **n8n**, HubSpot, Zapier, Make, or custom endpoints.

### Setup

Admin → **Configuration → Webhooks**:  
http://127.0.0.1:8001/admin/config-webhooks.html

1. Click **+ Add Webhook**.
2. **Name:** e.g. `HubSpot CRM`
3. **URL:** your endpoint (Zapier catch hook, Make webhook, etc.)
4. **Secret:** optional — sent as `X-Webhook-Signature` (HMAC-SHA256 of body)
5. **Events:** comma-separated, e.g. `brief.created, user.registered`
6. Save → click **Test** to send a `test.ping` event.

### n8n (recommended — free self-hosted)

n8n works with ATI outbound webhooks with **no code changes**. ATI sends a JSON `POST`; n8n’s Webhook trigger receives it.

**Cost:** Self-hosted n8n is free (Docker). n8n Cloud has paid tiers. ATI adds no per-event fee.

#### Prerequisites

- n8n running locally or on a server reachable from the ATI host
- Sample workflow in the repo: [`docs/n8n/ati-webhook-receiver.workflow.json`](docs/n8n/ati-webhook-receiver.workflow.json)
- Full import guide: [`docs/n8n/README.md`](docs/n8n/README.md)

#### Start n8n (Docker example)

```powershell
docker run -d --name n8n -p 5678:5678 -e ATI_WEBHOOK_SECRET=your-shared-secret n8nio/n8n
```

Open http://localhost:5678 and complete setup.

#### Wire ATI → n8n

1. n8n → **Workflows** → **Import from File** → select `docs/n8n/ati-webhook-receiver.workflow.json`
2. Open the **ATI Webhook** node → copy the **Production URL** (e.g. `http://localhost:5678/webhook/ati-onboarding`)
3. **Activate** the workflow (inactive workflows ignore production webhooks)
4. ATI admin → **Configuration → Webhooks**:

| Field | Example |
|-------|---------|
| Name | `n8n automation` |
| URL | Production URL from step 2 (not Test URL) |
| Secret | Same as `ATI_WEBHOOK_SECRET` in Docker (optional; enables HMAC verification) |
| Events | `brief.created, user.registered, session.created` |

5. Save → click **Test** → expect `test.ping` in n8n **Executions**
6. Confirm **Recent Deliveries** shows `delivered` on the ATI Webhooks page

#### Networking

| Setup | URL to use |
|-------|------------|
| ATI + n8n on same machine | `http://localhost:5678/webhook/ati-onboarding` |
| ATI on server, n8n elsewhere | Public `https://` n8n URL or tunnel (ngrok, Cloudflare) |

The ATI server must be able to reach the n8n URL. Localhost works only when both run on the same host.

#### n8n troubleshooting

| Symptom | Fix |
|---------|-----|
| No n8n executions | Activate workflow; use Production URL |
| ATI delivery `failed` | n8n down, wrong URL, or firewall |
| Invalid signature | Match Secret in ATI admin and `ATI_WEBHOOK_SECRET` in n8n |
| Live events missing | Add event name to ATI webhook **Events** field |

Replace the placeholder **NoOp** nodes in the sample workflow with CRM, Slack, or email nodes as needed.

### Sample `brief.created` payload

```json
{
  "event": "brief.created",
  "timestamp": "2026-06-08T12:00:00Z",
  "data": {
    "brief_id": "abc123",
    "ref_id": "Client_2026-06-08",
    "client_name": "Acme Corp",
    "user_email": "client@acme.com",
    "project_type": "website_development",
    "portal_link": "/portal.html?token=..."
  }
}
```

Copy the sample from **Configuration → Integrations** (`/admin/config-integrations.html`).

### Delivery log

On the Webhooks page, **Recent Deliveries** shows status, attempts, and errors for debugging.

---

## 9. Slack & Microsoft Teams

Admin → **Configuration → Integrations**:  
http://127.0.0.1:8001/admin/config-integrations.html

| Field | How to get |
|-------|------------|
| Slack Incoming Webhook URL | Slack app → Incoming Webhooks → Add to workspace |
| Teams Incoming Webhook URL | Teams channel → Connectors → Incoming Webhook |

Save integrations. All events dispatched via `notification_service` post a short text summary to these URLs when configured.

---

## 10. DocuSeal e-signature (optional)

For NDA signing after brief completion.

### Self-host DocuSeal (recommended)

```powershell
# Example with Docker — see https://github.com/docusealco/docuseal
docker run -d -p 3000:3000 docuseal/docuseal
```

1. Open DocuSeal admin → create an NDA template → note **Template ID**.
2. Settings → API → copy API key.

### Configure in ATI admin

**Configuration → Integrations**:

| Field | Example |
|-------|---------|
| API URL | `http://localhost:3000/api` |
| API Key | From DocuSeal settings |
| NDA Template ID | Numeric template ID |

### Send NDA for a brief

Admin → **Pipeline → Briefs** → use API:

```http
POST /api/admin/signatures/briefs/{brief_id}/nda
```

Requires admin permission on Briefs (update). DocuSeal emails the client a signing link.

---

## 11. Client portal & magic links

### Client portal (shareable brief link)

When a brief is created, the system generates a signed JWT portal token. Share:

```
http://127.0.0.1:8001/portal.html?token=<portal_token>
```

The client sees brief status and a download link **without logging in**. Tokens expire (default 30 days).

### Magic link (resume session)

API for passwordless session resume:

```http
POST /api/auth/magic-link
Content-Type: application/json

{
  "email": "user@example.com",
  "session_id": "<session-uuid>"
}
```

Sends `session_magic_link` email with a resume URL. Verify token:

```http
GET /api/auth/magic-link/verify?token=<jwt>
```

---

## 12. Admin RBAC & roles

### Default roles (seeded)

| Role | Sort order | Access |
|------|------------|--------|
| Super Admin | 1 | Full access |
| Admin | 2 | Full access |
| User | 3 | Dashboard, Pipeline, Reports (view) |

### Configure custom roles

Admin → **Settings → Role**:  
http://127.0.0.1:8001/admin/settings-roles.html

1. **+ Add Role** → name, description, permission matrix (modal).
2. Use presets: View only, Full access, Clear all.
3. Assign role to users under **Settings → User**.

### New admin pages (v3.9)

If Webhooks or Integrations are missing from the sidebar after upgrade, restart the server (seeders run `migrate_config_pages` on startup).

| Page | Path |
|------|------|
| Webhooks | `/admin/config-webhooks.html` |
| Integrations | `/admin/config-integrations.html` |

---

## 13. Verification checklist

Use this after a fresh install or deployment:

- [ ] `GET /health` returns `"status": "ok"` and Ollama models listed
- [ ] Login at `/login.html` with admin credentials
- [ ] Admin dashboard loads KPIs
- [ ] SMTP test email received
- [ ] System Config: management recipients set
- [ ] Register test user → `welcome` email received
- [ ] Complete test brief → `brief_ready` + `brief_submitted_admin` emails
- [ ] Paste an HTTPS reference URL in chat → **Research link** → agent summarizes page (after consent)
- [ ] Webhook test delivery shows `delivered` (if configured)
- [ ] `pytest tests/ -v` — all tests pass

```powershell
pytest tests/ -v
```

---

## 14. Troubleshooting

### Server / startup

| Symptom | Fix |
|---------|-----|
| MongoDB connection error | Check `MONGODB_URI`, IP whitelist, credentials |
| `ENCRYPTION_KEY` errors on SMTP save | Generate Fernet key — Section 2 |
| Admin pages 404 for new routes | Restart with `--reload` or full restart |
| Stale JS/CSS | Hard refresh (Ctrl+Shift+R); check `?v=` on script tags |

### Privacy & URL research

Reference links are fetched **only after consent** and **only over HTTPS** to public hosts (private IPs and localhost are blocked). Snapshots are saved to the client workspace and indexed for RAG — not stored as raw HTML in MongoDB. Disable via **Configuration → System Configuration → Allow reference link research**.

### Ollama / chat

| Symptom | Fix |
|---------|-----|
| `/health` degraded | Start Ollama; pull missing models |
| Wrong answers / mortgage drift | Re-index KB; check AI Configuration model |
| Slow responses | Normal for local SLM; consider `qwen2.5:7b` in AI Config |

### Email

| Symptom | Fix |
|---------|-----|
| No emails at all | System Config → Email notifications ON; SMTP configured |
| Client email only, no management alert | Set **Management To** in System Config |
| Template not found | Restart server to re-seed; check Email Templates page |

### Admin UI

| Symptom | Fix |
|---------|-----|
| Roles table empty on load | Hard refresh; ensure `settings-roles.js` v3.8.5+ |
| Permission denied on config pages | Check role permissions under Settings → Role |

---

## Related documentation

| File | Contents |
|------|----------|
| [README.md](README.md) | Project overview and quick start |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | Architecture, APIs, flowcharts |
| [docs/n8n/README.md](docs/n8n/README.md) | n8n webhook import and ATI wiring |
| [Run.txt](Run.txt) | Copy-paste commands |
| [.env.example](.env.example) | Environment variable template |
