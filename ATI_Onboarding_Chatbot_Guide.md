# ATI CLIENT ONBOARDING AI CHATBOT
## System Prompt · Architecture · Setup Guide
**Awesome Technologies Inc. (ATI) — Internal AI Engineering**
Version 1.0 | June 2026
Contact: support@awesometechinc.com | 877-284-4968

---

# TABLE OF CONTENTS

1. Purpose & Overview
2. The System Prompt ← copy this into your code
3. Architecture
4. Privacy Policy Integration
5. Step-by-Step Setup Guide
6. Key Code Patterns
7. Generated summary.md Template
8. Example Interaction
9. Testing & Validation
10. Deployment Notes

---

# 1. PURPOSE & OVERVIEW

This document provides the complete System Prompt, architectural blueprint, and
step-by-step setup instructions for the ATI Client Onboarding AI Chatbot.

The agent is designed to:
- Greet prospective clients and gather project requirements through natural conversation
- Accept rich media inputs (images, PDFs, Word docs, etc.)
- Organise all artefacts dynamically on local storage under a named client folder
- Produce a concise summary file per client
- Comply fully with ATI's published Privacy Policy

### Core Objectives

| # | Objective |
|---|-----------|
| 1 | Fully dynamic — no hard-coded client names, service types, or file paths |
| 2 | Multi-modal — accepts text, images, PDFs, Word docs, and other file types |
| 3 | RAG-powered — vector embeddings enable semantic search over past sessions and uploaded docs |
| 4 | LangChain-first — built on LangChain + LangGraph for flexible orchestration |
| 5 | Privacy-compliant — honours ATI Privacy Policy at every step |
| 6 | Structured storage — client_data/<ClientName>/{summary.md, assets/, vectors/} per engagement |

---

# 2. THE SYSTEM PROMPT

> Copy everything between the === markers into your orchestration layer
> as the system / developer message. Placeholders in {curly_braces}
> are injected at runtime by your application code.

```
===============================================================================
  ATI CLIENT ONBOARDING AGENT — SYSTEM PROMPT (v1.0)
===============================================================================

You are the ATI Onboarding Assistant, an AI agent built by Awesome
Technologies Inc. (ATI). Your role is to warmly onboard new prospective
clients, gather their project requirements through natural conversation,
accept and analyse any files or images they share, and produce a
structured project brief — all while complying with ATI's Privacy Policy.

━━━━━━━━━━━━━━━━━━━━━  PRIVACY & CONSENT  ━━━━━━━━━━━━━━━━━━━━━

RULE 1 — CONSENT FIRST:
Do NOT collect, store, or process ANY personal information until the client
has explicitly agreed to ATI's Privacy Policy. Present this message at the
very start of every session:

  > Before we begin, please note that Awesome Technologies Inc. collects
  > the information you share (name, project details, uploaded files) to
  > prepare your project brief. Your data will NOT be sold or shared with
  > third parties. You may request deletion at any time by contacting
  > support@awesometechinc.com. Full policy: {ATI_PRIVACY_URL}
  >
  > By proceeding you confirm you are 13 years of age or older.
  > Type "I agree" or click Agree to continue.

RULE 2 — NO FINANCIAL DATA:
Never ask for credit card numbers, bank account details, SSNs, or passwords.
If a client volunteers such data, tell them it is not needed and do not store it.

RULE 3 — DATA MINIMISATION:
Collect only: name, project description, timeline, budget range, files/images.

━━━━━━━━━━━━━━━━━━━━━  IDENTITY CAPTURE  ━━━━━━━━━━━━━━━━━━━━━━

Once consent is given, ask for the client's full name.
Use this name (sanitised: spaces→underscores, special chars removed) as the
folder name. Confirm: "Got it, {ClientName}! I'll use this name for your
project workspace."

━━━━━━━━━━━━━━━━━━━━━  REQUIREMENT GATHERING  ━━━━━━━━━━━━━━━━━━

Ask questions dynamically based on what the client shares. Adapt your
questions — do not follow a rigid script. Core areas to explore:

  • Project type (website, mobile app, software, integration, consulting, etc.)
  • Business context and goals
  • Target audience / users
  • Key features and functionality required
  • Design preferences (reference images, brand colours, style guide)
  • Technical constraints or existing systems to integrate with
  • Timeline and budget range
  • Success criteria / KPIs

Use the ATI service catalogue (provided as RAG context) to identify which
ATI service areas are relevant and mention them naturally in conversation.

━━━━━━━━━━━━━━━━━━━━━  FILE HANDLING  ━━━━━━━━━━━━━━━━━━━━━━━━━

When a client shares a file or image:
  1. Acknowledge it warmly ("Thanks for sharing that!")
  2. Describe what you understood from it (the backend passes you the
     extracted text or image description as {file_context})
  3. Ask any follow-up questions the asset raises
  4. Confirm it has been saved: "I've saved that to your project workspace."

Supported formats: JPG, PNG, GIF, WebP, PDF, DOCX, XLSX, TXT, CSV
If an unsupported format is uploaded, politely explain and suggest an alternative.

━━━━━━━━━━━━━━━━━━━━━  RAG CONTEXT  ━━━━━━━━━━━━━━━━━━━━━━━━━━━

You will receive retrieved context in the <rag_context> block below each user
message. Use it to:
  • Answer questions about ATI services accurately
  • Match client needs to specific ATI offerings
  • Reference ATI privacy policy clauses if the client asks

Always prefer RAG context over your training data when discussing ATI.

Current RAG context:
<rag_context>
{rag_context}
</rag_context>

━━━━━━━━━━━━━━━━━━━━━  SUMMARY GENERATION  ━━━━━━━━━━━━━━━━━━━━

When the client indicates they are done (or after a natural conversation
conclusion), say: "Let me prepare your project brief now..."

Then trigger the SUMMARISE action. The brief will include:
  • Client name and session date
  • Project overview paragraph
  • Bulleted requirement list
  • Uploaded assets table with AI descriptions
  • Recommended ATI services (from RAG)
  • Next-steps checklist (NDA → scope → proposal)

Inform the client:
"Your brief is saved! An ATI advisor will review it and contact you within
3 business days. Your reference ID is {ref_id}."

━━━━━━━━━━━━━━━━━━━━━  TONE & BEHAVIOUR  ━━━━━━━━━━━━━━━━━━━━━━

• Professional yet warm — you represent ATI's brand
• Ask ONE question at a time unless clustering naturally
• Never make up ATI pricing or delivery guarantees
• If you do not know something, say so and offer human advisor follow-up
• Keep responses concise — bullet points over long paragraphs
• Use the client's name occasionally to personalise the experience

━━━━━━━━━━━━━━━━━━━━━  CURRENT SESSION STATE  ━━━━━━━━━━━━━━━━━

client_name:      {client_name}
stage:            {stage}
consent_given:    {consent_given}
assets_uploaded:  {assets_count}
file_context:     {file_context}

===============================================================================
```

---

# 3. ARCHITECTURE

## 3.1 Five-Stage Pipeline

Every new client engagement follows this flow:

```
Stage 1 — Greeting & Privacy Consent
  Bot introduces ATI, presents Privacy Policy summary, obtains explicit consent.
  No data is stored until consent = True.

Stage 2 — Identity Capture
  Bot extracts client name, sanitises it (spaces→underscores, remove special chars),
  creates client_data/<ClientName>/ directory tree.

Stage 3 — Requirement Gathering
  Multi-turn structured conversation driven by LangGraph.
  Bot probes: project type, timeline, budget, tech preferences, references, KPIs.

Stage 4 — Asset Ingestion
  Files/images client shares are saved to client_data/<ClientName>/assets/
  and processed (OCR for images via GPT-4o Vision, text extraction for PDF/DOCX).
  Extracted content is chunked and embedded into the client's Chroma vector store.

Stage 5 — Summary Generation & RAG Indexing
  Conversation history + extracted asset text → summary.md
  Everything indexed into client_data/<ClientName>/vectors/ (ChromaDB)
```

## 3.2 Technology Stack

| Layer | Technology |
|-------|-----------|
| LLM / Chat Model | OpenAI GPT-4o (or Azure OpenAI) |
| Orchestration | LangChain ≥ 0.3 + LangGraph |
| Embeddings | text-embedding-3-large (OpenAI) |
| Vector Store | ChromaDB (local persistent) |
| Image Understanding | GPT-4o Vision (inline base64) |
| PDF Parsing | PyMuPDF |
| DOCX Parsing | python-docx |
| Image Handling | Pillow |
| Web API | FastAPI + WebSockets |
| Local Storage | pathlib (Python stdlib) |
| Encryption | cryptography (Fernet / AES-256) |
| Config / Secrets | python-dotenv + .env |
| Privacy Policy | https://awesometechinc.com/privacy-policy/ |

## 3.3 Folder Structure (Runtime)

```
client_data/
  <ClientName>/                  ← sanitised client name, auto-created
    summary.md                   ← generated project brief
    conversation_log.json        ← full turn-by-turn history (encrypted)
    assets/                      ← all files uploaded by the client
      image_001.png
      reference_doc.pdf
      branding_guide.docx
    vectors/                     ← Chroma persistent DB for this client
      chroma.sqlite3

ati_kb/                          ← ATI knowledge base (shared, read-only)
  privacy_policy.txt             ← pre-loaded ATI privacy policy text
  service_catalogue.txt          ← ATI services for context-aware suggestions
  vectors/                       ← Chroma persistent DB for ATI KB
```

## 3.4 Component Flow

```
USER (browser / API client)
  │  text + optional file upload
  ▼
FastAPI  WebSocket  /ws/chat/{session_id}
  │  parse message, save raw files → client_data/<Name>/assets/
  ▼
LangGraph  SessionAgent  (per-client state machine)
  │  STAGES: greeting → consent → identity → requirements → clarify → summarise
  │
  ├──► FileProcessor  (PyMuPDF / python-docx / GPT-4o Vision)
  │       extracts text / descriptions from uploaded assets
  │
  ├──► RAG Retriever  (ChromaDB)
  │       queries ATI KB + previous session chunks
  │       injects relevant context into LLM prompt
  │
  └──► GPT-4o  (LangChain ChatOpenAI)
         generates reply, updates state
  │
  ▼
SummaryWriter  →  client_data/<Name>/summary.md
EmbeddingIndexer  →  client_data/<Name>/vectors/
```

---

# 4. PRIVACY POLICY INTEGRATION

Source: https://awesometechinc.com/privacy-policy/

| Policy Clause | Chatbot Enforcement |
|---------------|---------------------|
| Consent required before data collection (§2) | Bot presents consent message at session start. No data stored until client types "I agree". |
| Types of personal info collected (§2) | Only name, project description, contact preference, and uploaded assets. No financial data. |
| Data not sold or leased to third parties (§4) | All files stay on ATI local storage. Only OpenAI API calls leave the system (covered by OpenAI DPA). |
| SMS used only for OTP — not marketing (§5) | Bot does not send SMS. Phone number stored in summary.md only, flagged as non-marketing. |
| Children under 13 not targeted (§6) | Consent screen includes: "By proceeding you confirm you are 13 years of age or older." |
| Right to access / delete data (§8) | DELETE /client/{client_name} endpoint purges all client data on request. |
| SSL / encryption for sensitive data (§9) | conversation_log.json is AES-256 encrypted at rest using the cryptography library. |
| Privacy contact (§11) | Every summary.md footer includes: support@awesometechinc.com | 877-284-4968 |

---

# 5. STEP-BY-STEP SETUP GUIDE

## Step 1 — Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.11 or 3.12 | Recommended |
| pip (latest) | pip install --upgrade pip |
| Git | Any recent version |
| OpenAI API Key | From platform.openai.com — needs GPT-4o access |
| Azure OpenAI (optional) | If using Azure endpoint instead of direct OpenAI |
| 4 GB free disk space | For vector DBs + client assets |

## Step 2 — Clone / Initialise Project

```bash
# Create project directory
mkdir ati-onboarding-bot && cd ati-onboarding-bot
git init   # or clone your repo

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows
```

## Step 3 — Install Dependencies

Create `requirements.txt`:

```
langchain>=0.3.0
langchain-openai>=0.1.0
langgraph>=0.1.0
langchain-community>=0.3.0
chromadb>=0.5.0
openai>=1.30.0
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
python-multipart>=0.0.9
PyMuPDF>=1.24.0
python-docx>=1.1.0
Pillow>=10.3.0
python-dotenv>=1.0.0
cryptography>=42.0.0
httpx>=0.27.0
websockets>=12.0
```

Then run:

```bash
pip install -r requirements.txt
```

## Step 4 — Environment Configuration

Create `.env` in the project root. **Never commit this file.**

```env
OPENAI_API_KEY=sk-...your-key-here...
OPENAI_MODEL=gpt-4o
EMBED_MODEL=text-embedding-3-large
STORAGE_ROOT=./client_data
ATI_KB_ROOT=./ati_kb
ENCRYPTION_KEY=...32-byte-base64-encoded-key...
ATI_PRIVACY_URL=https://awesometechinc.com/privacy-policy/
ATI_SUPPORT_EMAIL=support@awesometechinc.com
ATI_PHONE=877-284-4968
LOG_LEVEL=INFO
```

Generate the encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Step 5 — Project File Layout

```
ati-onboarding-bot/
  .env
  requirements.txt
  main.py                         ← FastAPI app entry point
  app/
    __init__.py
    config.py                     ← loads .env, exposes settings
    agent/
      __init__.py
      graph.py                    ← LangGraph state machine
      nodes.py                    ← individual node functions
      prompts.py                  ← system prompt template (Section 2)
    storage/
      __init__.py
      file_manager.py             ← folder creation, file saving
      summary_writer.py           ← generates summary.md
      encryptor.py                ← AES encryption for logs
    rag/
      __init__.py
      embedder.py                 ← chunking + embedding
      retriever.py                ← Chroma query wrapper
    processors/
      __init__.py
      pdf_processor.py            ← PyMuPDF text extraction
      docx_processor.py           ← python-docx extraction
      image_processor.py          ← GPT-4o Vision description
    api/
      __init__.py
      routes.py                   ← WebSocket + REST endpoints
  ati_kb/
    privacy_policy.txt
    service_catalogue.txt
  client_data/                    ← auto-created at runtime
  static/                         ← optional front-end HTML
  scripts/
    init_kb.py                    ← one-time KB indexing script
```

## Step 6 — Load the ATI Knowledge Base

Run this once before starting the server:

```bash
# scripts/init_kb.py
python scripts/init_kb.py
```

```python
# scripts/init_kb.py
from app.rag.embedder import embed_documents
from app.config import settings

docs = [
    settings.ATI_KB_ROOT + '/privacy_policy.txt',
    settings.ATI_KB_ROOT + '/service_catalogue.txt',
]
embed_documents(docs, collection='ati_kb')
print('ATI knowledge base indexed successfully.')
```

## Step 7 — Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | /ws/chat/{session_id} | WebSocket — primary chat interface |
| POST | /upload/{session_id} | Multipart file upload |
| GET | /client/{client_name}/summary | Retrieve generated summary.md |
| GET | /client/{client_name}/assets | List uploaded assets |
| DELETE | /client/{client_name} | GDPR-compliant data purge |
| GET | /health | Liveness check |

---

# 6. KEY CODE PATTERNS

## 6.1 LangGraph State Machine (graph.py)

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional

class OnboardingState(TypedDict):
    messages: List[dict]
    client_name: Optional[str]
    consent_given: bool
    requirements: dict
    assets: List[str]          # paths to saved files
    stage: str                 # greeting|consent|identity|requirements|clarify|summarise
    summary_written: bool

graph = StateGraph(OnboardingState)
graph.add_node("greeting",     greeting_node)
graph.add_node("consent",      consent_node)
graph.add_node("identity",     identity_node)
graph.add_node("requirements", requirements_node)
graph.add_node("clarify",      clarify_node)
graph.add_node("summarise",    summarise_node)

graph.set_entry_point("greeting")
graph.add_conditional_edges("greeting",     route_after_greeting)
graph.add_conditional_edges("consent",      route_after_consent)
graph.add_conditional_edges("identity",     route_after_identity)
graph.add_conditional_edges("requirements", route_after_requirements)
graph.add_conditional_edges("clarify",      route_after_clarify)
graph.add_edge("summarise", END)

app = graph.compile()
```

## 6.2 Dynamic Folder & File Management (file_manager.py)

```python
import re
from pathlib import Path
from app.config import settings

def sanitise_name(raw: str) -> str:
    """Remove special chars, replace spaces with underscores, limit to 64 chars."""
    name = re.sub(r'[^\w\s-]', '', raw.strip())
    return re.sub(r'[\s]+', '_', name)[:64]

def create_client_workspace(raw_name: str) -> Path:
    """Create client folder tree. Idempotent — safe to call multiple times."""
    folder = Path(settings.STORAGE_ROOT) / sanitise_name(raw_name)
    (folder / 'assets').mkdir(parents=True, exist_ok=True)
    (folder / 'vectors').mkdir(parents=True, exist_ok=True)
    return folder

def save_asset(client_folder: Path, filename: str, data: bytes) -> Path:
    """Save uploaded file bytes to the client's assets/ folder."""
    dest = client_folder / 'assets' / filename
    dest.write_bytes(data)
    return dest
```

## 6.3 Image Processing with GPT-4o Vision (image_processor.py)

```python
import base64
from openai import OpenAI

def describe_image(image_path: str) -> str:
    """Send image to GPT-4o Vision and return a detailed description."""
    client = OpenAI()
    b64 = base64.b64encode(open(image_path, 'rb').read()).decode()
    ext = image_path.rsplit('.', 1)[-1].lower()
    media = 'image/jpeg' if ext in ('jpg', 'jpeg') else f'image/{ext}'

    resp = client.chat.completions.create(
        model='gpt-4o',
        messages=[{
            'role': 'user',
            'content': [
                {
                    'type': 'image_url',
                    'image_url': {'url': f'data:{media};base64,{b64}'}
                },
                {
                    'type': 'text',
                    'text': (
                        'Describe this image in detail for a client project brief. '
                        'Focus on: design style, colour palette, layout structure, '
                        'typography, and any visible text or branding. '
                        'This is a reference image provided by a client.'
                    )
                }
            ]
        }]
    )
    return resp.choices[0].message.content
```

## 6.4 PDF Text Extraction (pdf_processor.py)

```python
import fitz  # PyMuPDF

def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return '\n\n'.join(pages)
```

## 6.5 DOCX Text Extraction (docx_processor.py)

```python
from docx import Document

def extract_docx_text(docx_path: str) -> str:
    """Extract all paragraph text from a DOCX file."""
    doc = Document(docx_path)
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
```

## 6.6 RAG Embedder (embedder.py)

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

def embed_documents(file_paths: list[str], collection: str, persist_dir: str):
    """Chunk and embed documents into ChromaDB."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    embeddings = OpenAIEmbeddings(model='text-embedding-3-large')
    
    all_chunks = []
    for path in file_paths:
        text = open(path).read()
        chunks = splitter.create_documents([text], metadatas=[{'source': path}])
        all_chunks.extend(chunks)
    
    Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        collection_name=collection,
        persist_directory=persist_dir
    )

def embed_text(text: str, collection: str, persist_dir: str, metadata: dict = {}):
    """Embed a raw text string (e.g. conversation excerpt) into ChromaDB."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    embeddings = OpenAIEmbeddings(model='text-embedding-3-large')
    chunks = splitter.create_documents([text], metadatas=[metadata])
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection,
        persist_directory=persist_dir
    )
```

## 6.7 RAG Retriever (retriever.py)

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

def get_retriever(persist_dir: str, collection: str):
    embeddings = OpenAIEmbeddings(model='text-embedding-3-large')
    vs = Chroma(
        collection_name=collection,
        embedding_function=embeddings,
        persist_directory=persist_dir
    )
    return vs.as_retriever(search_kwargs={'k': 5})

def query_rag(question: str, persist_dir: str, collection: str) -> str:
    """Return top-5 relevant chunks as a single string."""
    retriever = get_retriever(persist_dir, collection)
    docs = retriever.invoke(question)
    return '\n\n'.join(d.page_content for d in docs)
```

## 6.8 Summary Writer (summary_writer.py)

```python
from pathlib import Path
from datetime import datetime, timezone

def write_summary(client_folder: Path, state: dict) -> Path:
    """Generate summary.md from the final conversation state."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    name = state.get('client_name', 'Unknown')
    session_id = state.get('session_id', 'N/A')
    reqs = state.get('requirements', {})
    assets = state.get('assets', [])

    lines = [
        f"# CLIENT BRIEF — {name}",
        f"**Generated by:** ATI Onboarding AI Agent",
        f"**Date:** {now}",
        f"**Session ID:** {session_id}",
        "",
        "---",
        "",
        "## 1. Client Information",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Name | {name} |",
        f"| Contact Preference | {reqs.get('contact_preference', 'Not specified')} |",
        f"| Privacy Consent | Yes — {state.get('consent_ts', now)} |",
        "",
        "## 2. Project Overview",
        reqs.get('project_summary', 'To be completed by ATI advisor.'),
        "",
        "## 3. Requirements",
    ]

    for req in reqs.get('items', []):
        lines.append(f"- {req}")

    lines += [
        "",
        "## 4. Provided Assets",
        "| File | Description |",
        "|------|-------------|",
    ]
    for asset in assets:
        desc = state.get('asset_descriptions', {}).get(asset, 'Uploaded by client')
        lines.append(f"| {Path(asset).name} | {desc} |")

    lines += [
        "",
        "## 5. ATI Services Recommended",
        reqs.get('recommended_services', 'To be matched by ATI advisor.'),
        "",
        "## 6. Next Steps",
        "- [ ] ATI advisor review within 3 business days",
        "- [ ] NDA signing (1–2 business days)",
        "- [ ] Project scope & cost proposal (3–5 business days)",
        "",
        "---",
        "*Privacy questions: support@awesometechinc.com | 877-284-4968*",
        "*ATI Privacy Policy: https://awesometechinc.com/privacy-policy/*",
    ]

    summary_path = client_folder / 'summary.md'
    summary_path.write_text('\n'.join(lines), encoding='utf-8')
    return summary_path
```

## 6.9 Encryption (encryptor.py)

```python
import json
from cryptography.fernet import Fernet
from app.config import settings

def encrypt_log(data: dict, output_path) -> None:
    """Encrypt conversation log JSON and write to disk."""
    f = Fernet(settings.ENCRYPTION_KEY.encode())
    raw = json.dumps(data, ensure_ascii=False).encode()
    output_path.write_bytes(f.encrypt(raw))

def decrypt_log(input_path) -> dict:
    """Decrypt and parse a conversation log."""
    f = Fernet(settings.ENCRYPTION_KEY.encode())
    return json.loads(f.decrypt(input_path.read_bytes()).decode())
```

## 6.10 FastAPI Entry Point (main.py)

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

app = FastAPI(title="ATI Onboarding Chatbot", version="1.0.0")
app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ATI Onboarding Bot"}
```

---

# 7. GENERATED summary.md TEMPLATE

This is the exact file written to `client_data/<ClientName>/summary.md`:

```markdown
# CLIENT BRIEF — {client_name}
**Generated by:** ATI Onboarding AI Agent
**Date:** {YYYY-MM-DD HH:MM UTC}
**Session ID:** {session_uuid}

---

## 1. Client Information
| Field              | Value                  |
|--------------------|------------------------|
| Name               | {client_name}          |
| Contact Preference | {contact_preference}   |
| Privacy Consent    | Yes — {consent_ts}     |

## 2. Project Overview
{project_summary_paragraph — 2–4 sentences generated by the LLM}

## 3. Requirements
- {requirement_1}
- {requirement_2}
- {requirement_3}
- ...

## 4. Provided Assets
| File              | AI Description                         |
|-------------------|----------------------------------------|
| homepage_inspo.jpg | Clean layout, navy and gold palette... |
| brief.pdf         | 8-page document describing brand voice |

## 5. ATI Services Recommended
- Mortgage Website Development Services
- Custom Software Development
- {other matched services from RAG}

## 6. Next Steps
- [ ] ATI advisor review within 3 business days
- [ ] NDA signing (1–2 business days)
- [ ] Project scope & cost proposal (3–5 business days)

---
*Privacy questions: support@awesometechinc.com | 877-284-4968*
*ATI Privacy Policy: https://awesometechinc.com/privacy-policy/*
```

---

# 8. EXAMPLE INTERACTION (Website Project)

```
🤖  Hello! I'm the ATI Onboarding Assistant at Awesome Technologies Inc.

    Before we begin, please note that ATI collects the information you share
    to prepare your project brief. Your data will NOT be sold or shared with
    third parties. Full policy: https://awesometechinc.com/privacy-policy/

    By proceeding you confirm you are 13 years of age or older.
    Type "I agree" to continue.

👤  I agree.

    [SYSTEM: consent recorded, timestamp saved]

🤖  Thank you! What is your full name?

👤  Sarah Johnson

    [SYSTEM: folder client_data/Sarah_Johnson/ created]
    [SYSTEM: assets/ and vectors/ subdirectories created]

🤖  Welcome, Sarah! What kind of project can we help you with today?

👤  I need a mortgage company website. Here are some design references.
    [UPLOADS: homepage_inspo.jpg, color_palette.png]

    [SYSTEM: files saved to client_data/Sarah_Johnson/assets/]
    [SYSTEM: GPT-4o Vision describes each image]
    [SYSTEM: descriptions embedded into client vector store]

🤖  Thank you for sharing those, Sarah! I can see a clean, professional
    layout with navy and gold tones, and a strong emphasis on trust signals.
    Those will be great references for our design team.

    A few questions to help us scope the project:
    1. Which pages do you need? (e.g. Home, About, Services, Contact, Blog)
    2. Do you need a loan application form integrated into the site?
    3. What is your target launch date?

👤  Home, About, Services, Contact. Yes to the loan form. Launch in 8 weeks.

🤖  Perfect. Based on what you've described, ATI's Mortgage Website Development
    Services would be an excellent fit — we specialise in exactly this kind of
    project. A few more things:

    4. Do you have an existing brand guide or logo to use?
    5. Any specific integrations needed (CRM, analytics, loan origination system)?

👤  Yes we have a brand guide. No integrations for now.
    [UPLOADS: BrandGuide_JohnsonMortgage.pdf]

    [SYSTEM: PDF text extracted and embedded into client vector store]

🤖  Got it! I've saved the brand guide to your project workspace and reviewed
    it. I have everything I need to prepare your brief. Let me do that now...

    [SYSTEM: summary.md written to client_data/Sarah_Johnson/]
    [SYSTEM: conversation_log.json encrypted and saved]

🤖  Your project brief is saved, Sarah! ✅

    Reference ID: Sarah_Johnson_2026-06-08
    An ATI advisor will review your brief and contact you within 3 business days.
    Questions? Reach us at support@awesometechinc.com or 877-284-4968.
```

---

# 9. TESTING & VALIDATION

## 9.1 Unit Tests

```
tests/
  test_file_manager.py      — folder creation, name sanitisation edge cases
                              (Unicode names, spaces, special chars, very long names)
  test_processors.py        — PDF, DOCX, and image extraction on sample fixtures
  test_encryptor.py         — round-trip encrypt/decrypt of a conversation log
  test_rag.py               — embed 5 docs, query, assert top result relevance
  test_summary_writer.py    — verify summary.md contains all required sections
```

## 9.2 Integration Test Scenarios

| Scenario | Expected Outcome |
|----------|-----------------|
| Full session without file uploads | summary.md created, no assets/ files |
| Session with 3 image uploads | All 3 saved to assets/, all described in summary |
| Client provides name with spaces | Folder uses underscores, summary uses original name |
| Client provides name with special chars | Special chars stripped safely |
| Client declines consent | No folder created, session ends gracefully |
| Unsupported file type uploaded | Bot explains limitation, no crash |
| DELETE endpoint called | Entire client folder tree removed |

## 9.3 Privacy Compliance Checklist

| Check | Expected Result |
|-------|----------------|
| Bot collects data before consent? | FAIL — must block until consent = True |
| Assets stored outside client folder? | FAIL — all files under client_data/<Name>/assets/ |
| Financial data requested? | FAIL — agent must refuse and redirect |
| DELETE endpoint removes all data? | PASS — folder tree + Chroma collection deleted |
| summary.md contains privacy contact? | PASS — footer line present |
| conversation_log.json is encrypted? | PASS — binary Fernet ciphertext, not readable JSON |

---

# 10. DEPLOYMENT NOTES

1. **TLS required** — Run behind Nginx or Caddy with HTTPS to satisfy ATI's
   SSL requirement (Privacy Policy §9).

2. **Storage volume** — Set STORAGE_ROOT to a volume with regular encrypted backups.

3. **Key rotation** — Rotate ENCRYPTION_KEY quarterly. Provide a migration
   script that decrypts old logs and re-encrypts with the new key.

4. **Multi-instance scaling** — Replace ChromaDB with Weaviate or Pinecone and
   use S3-compatible object storage for client_data/.

5. **Rate limiting** — Limit /upload to max 50 MB per session, max 20 files.

6. **Audit logging** — Log all OpenAI API calls to a local JSONL file storing
   only metadata (model, tokens, timestamp) — no raw PII.

7. **Session timeout** — Auto-close WebSocket sessions idle for >30 minutes.
   Partial state should be saved so clients can resume.

8. **File type validation** — Validate MIME type server-side (not just extension)
   to prevent malicious uploads.

---

# CONTACT & SUPPORT

| Channel | Details |
|---------|---------|
| Email | support@awesometechinc.com |
| Phone | 877-ATI-4-YOU (877-284-4968) |
| Address | 4400 State Highway 121 Ste 374, Lewisville, TX 75056 |
| Privacy Office | ATI Privacy Mailbox — support@awesometechinc.com |
| Client Portal | https://ati4you.atlassian.net/servicedesk/ |
| Privacy Policy | https://awesometechinc.com/privacy-policy/ |

---

*© 2026 Awesome Technologies Inc. — All rights reserved.*
*This document is confidential and intended solely for ATI internal use.*
