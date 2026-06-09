import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from app.agent.graph import process_message, run_agent_step
from app.agent.task_router import get_suggestions
from app.config import settings
from app.processors.file_router import is_supported, process_file
from app.rag.embedder import embed_text
from app.storage.file_manager import (
    create_client_workspace,
    delete_client_data,
    get_summary_path,
    list_assets,
    save_asset,
    sanitise_name,
)
from app.storage.session_store import session_store

logger = logging.getLogger(__name__)
router = APIRouter()

_agent_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ati-agent")
_session_upload_counts: dict[str, int] = {}
_session_upload_sizes: dict[str, int] = {}


def _run_agent_step_sync(session_id: str, user_message: str | None = None) -> dict:
    state = session_store.get(session_id)
    if user_message is None:
        state = run_agent_step(state)
    else:
        state = process_message(state, user_message)
    session_store.update(session_id, state)
    return state


async def _run_agent_step(session_id: str, user_message: str | None = None) -> dict:
    loop = asyncio.get_running_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(
            _agent_executor,
            _run_agent_step_sync,
            session_id,
            user_message,
        ),
        timeout=45.0,
    )


def _reply_content(state: dict) -> str:
    if state.get("pending_reply"):
        return state["pending_reply"]
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "assistant" and msg.get("content"):
            return msg["content"]
    return (
        "Hello! I'm the ATI Onboarding Assistant. "
        'Please type "I agree" or click Agree to continue.'
    )


async def _send_assistant_reply(websocket: WebSocket, state: dict) -> None:
    content = _reply_content(state)
    stage = state.get("stage", "consent")
    await websocket.send_json({
        "type": "message",
        "role": "assistant",
        "content": content,
        "stage": stage,
        "done": state.get("done", False),
        "ref_id": state.get("ref_id"),
        "suggestions": get_suggestions(stage, state.get("client_name")),
        "consent_given": state.get("consent_given", False),
        "client_name": state.get("client_name"),
        "assets_count": len(state.get("assets", [])),
    })


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    state = session_store.get(session_id)

    try:
        if not state.get("messages"):
            state = await _run_agent_step(session_id)
            logger.info("Sent greeting to session %s", session_id)
        else:
            logger.info("Syncing state to reconnected session %s", session_id)
        await _send_assistant_reply(websocket, state)
    except Exception:
        logger.exception("Error sending initial greeting for session %s", session_id)
        await websocket.send_json({
            "type": "message",
            "role": "assistant",
            "content": (
                "Hello! I'm the ATI Onboarding Assistant. "
                'Please type "I agree" or click Agree to continue.'
            ),
            "stage": "consent",
            "suggestions": ["I agree"],
            "consent_given": False,
        })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                user_message = payload.get("message", data)
                action = payload.get("action")
            except json.JSONDecodeError:
                user_message = data
                action = None

            if action == "agree":
                user_message = "I agree"

            logger.info("Received message for session %s: %s", session_id, user_message[:50])

            try:
                state = await _run_agent_step(session_id, user_message)
                await _send_assistant_reply(websocket, state)
                logger.info("Sent reply to session %s, stage=%s", session_id, state.get("stage"))
            except asyncio.TimeoutError:
                logger.error("Agent timed out for session %s", session_id)
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": (
                        "Sorry, that took too long. Please try again. "
                        "If this keeps happening, restart the server."
                    ),
                    "stage": "error",
                    "suggestions": [],
                })
            except Exception:
                logger.exception("Error processing message for session %s", session_id)
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": (
                        "Sorry, something went wrong processing your message. "
                        "Please try again."
                    ),
                    "stage": "error",
                    "suggestions": [],
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session_id)


@router.post("/upload/{session_id}")
async def upload_file(session_id: str, file: UploadFile = File(...)):
    state = session_store.get(session_id)

    if not state.get("consent_given"):
        raise HTTPException(status_code=403, detail="Consent required before uploading files")

    if not state.get("client_name"):
        raise HTTPException(status_code=400, detail="Please provide your name before uploading files")

    if not is_supported(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Supported: JPG, PNG, GIF, WebP, PDF, DOCX, XLSX, TXT, CSV",
        )

    file_count = _session_upload_counts.get(session_id, 0)
    if file_count >= settings.MAX_FILES_PER_SESSION:
        raise HTTPException(status_code=400, detail=f"Maximum {settings.MAX_FILES_PER_SESSION} files per session")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    total_size = _session_upload_sizes.get(session_id, 0) + len(content)
    if total_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Maximum {settings.MAX_UPLOAD_SIZE_MB} MB per session")

    client_folder = create_client_workspace(state["client_name"])
    saved_path = save_asset(client_folder, file.filename or "upload", content)

    try:
        extracted, proc_type = process_file(str(saved_path))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("File processing failed")
        extracted = f"[Processing error: {e}]"
        proc_type = "error"

    state["assets"].append(str(saved_path))
    state["asset_descriptions"][str(saved_path)] = extracted[:500]

    collection_name = f"client_{sanitise_name(state['client_name'])}"
    embed_text(
        extracted,
        collection_name,
        client_folder / "vectors",
        metadata={"source": str(saved_path), "type": proc_type},
    )

    state["file_context"] = (
        f"File: {saved_path.name}\nType: {proc_type}\nContent/Description: {extracted[:2000]}"
    )
    session_store.update(session_id, state)

    _session_upload_counts[session_id] = file_count + 1
    _session_upload_sizes[session_id] = total_size

    return {
        "status": "saved",
        "filename": saved_path.name,
        "path": str(saved_path),
        "processing_type": proc_type,
        "description_preview": extracted[:200],
    }


@router.get("/client/{client_name}/summary")
async def get_summary(client_name: str):
    summary_path = get_summary_path(client_name)
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Summary not found for this client")
    return {"client_name": client_name, "summary": summary_path.read_text(encoding="utf-8")}


@router.get("/client/{client_name}/assets")
async def get_assets(client_name: str):
    folder = settings.client_folder(client_name)
    if not folder.exists():
        raise HTTPException(status_code=404, detail="Client not found")
    return {"client_name": client_name, "assets": list_assets(folder)}


@router.delete("/client/{client_name}")
async def delete_client(client_name: str):
    deleted = delete_client_data(client_name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"status": "deleted", "client_name": client_name}
