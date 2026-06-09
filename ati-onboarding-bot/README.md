# ATI Client Onboarding AI Chatbot

An AI-powered onboarding assistant for Awesome Technologies Inc. (ATI) that gathers project requirements through natural conversation, accepts file uploads, and generates structured client briefs.

Built with **FastAPI**, **LangGraph**, **ChromaDB RAG**, **Ollama (local SLMs)**, and **React + Vite**.

**No API keys. No quota limits. Runs 100% free locally.**

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.11 or 3.12 | [python.org/downloads](https://www.python.org/downloads/) |
| Node.js 18+ | For React frontend build |
| Ollama | [ollama.com/download](https://ollama.com/download) |
| 8+ GB RAM | For chat + vision models |

---

## One-Time Setup

### 1. Install Ollama and pull models

```powershell
# Install Ollama from https://ollama.com/download, then:
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
ollama pull llava
```

### 2. Python environment

```powershell
cd "C:\Users\Asus\Desktop\Awesome Technologies\ati-onboarding-bot"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure `.env`

```powershell
copy .env.example .env
```

Generate encryption key:
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Verify Ollama

```powershell
python scripts/check_ollama.py
```

### 5. Index knowledge base (re-run after KB changes)

```powershell
Remove-Item -Recurse -Force ati_kb\vectors -ErrorAction SilentlyContinue
python scripts/init_kb.py
```

### 6. Build React frontend

```powershell
cd frontend
npm install
npm run build
cd ..
```

---

## Run

```powershell
.venv\Scripts\activate
uvicorn main:app --host 127.0.0.1 --port 8001
```

Open [http://127.0.0.1:8001](http://127.0.0.1:8001)

### Development (hot reload frontend)

```powershell
# Terminal 1 — backend
uvicorn main:app --host 127.0.0.1 --port 8001

# Terminal 2 — frontend
cd frontend && npm run dev
```

Frontend dev server: [http://127.0.0.1:5173](http://127.0.0.1:5173) (proxies API to :8001)

---

## Architecture

| Stage | Method | Model |
|-------|--------|-------|
| Consent, Identity | Rule-based | None |
| Requirements, Clarify | SLM + RAG | `qwen2.5:3b` + ChromaDB |
| Summarise | SLM + RAG | `qwen2.5:3b` |
| Embeddings | Local | `nomic-embed-text` |
| Image vision | Local | `llava` |
| PDF/DOCX/TXT | Parsers | PyMuPDF, python-docx |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/ws/chat/{session_id}` | WebSocket chat |
| POST | `/upload/{session_id}` | File upload |
| GET | `/client/{name}/summary` | Retrieve brief |
| GET | `/client/{name}/assets` | List assets |
| DELETE | `/client/{name}` | Purge client data |
| GET | `/health` | Health + Ollama status |

---

## UI Features

- 5-step progress stepper (Consent → Name → Project → Files → Brief)
- Quick-reply suggestion chips
- Consent card with privacy policy link
- Drag-and-drop file upload with previews
- Typing indicator
- Clickable links in messages

---

## Tests

```powershell
pytest tests/ -v
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Ollama not reachable | Run `ollama serve` or restart Ollama app |
| Missing models | `ollama pull qwen2.5:3b` etc. |
| Slow first response | Normal — model loads on first call (~10s). Run `check_ollama.py` to warm up |
| Port 8000 busy | Use port 8001 (Apache may use 8000) |
| RAG returns nothing | Re-run `python scripts/init_kb.py` after deleting `ati_kb/vectors` |

---

## Support

- Email: support@awesometechinc.com
- Phone: 877-284-4968
- Privacy: https://awesometechinc.com/privacy-policy/
