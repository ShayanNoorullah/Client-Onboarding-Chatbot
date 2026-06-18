import asyncio
import hashlib
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from app.api.schemas import SurfUrlRequest

from app.agent.graph import process_message, request_manual_brief, run_agent_step
from app.agent.field_extractor import merge_collected_requirements
from app.agent.session_memory import maybe_update_session_summary
from app.agent.term_glossary import expand_terms
from app.agent.routing import can_request_manual_brief
from app.agent.nodes import greeting_node, is_modal_consent_phrase, proactive_clarify_after_upload, proactive_clarify_after_surf, record_modal_consent
from app.agent.task_router import get_suggestions
from app.auth.dependencies import get_current_user, get_ws_user
from app.config import settings
from app.models.user import User
from app.models.brief import Brief
from app.services.agent_metrics import metrics, timed
from app.processors.file_router import is_supported, process_file
from app.rag.embedder import embed_text
from app.services.brief_service import persist_brief_to_mongo
from app.services.feedback_service import ingest_feedback, record_turn, task_type_for_stage
from app.services.learning_constraints_service import build_learned_constraints_text
from app.services.learning_service import (
    extract_and_store_facts,
    get_user_memory_context,
    learn_from_completed_session,
    store_correction_fact,
)
from app.services.prompt_registry import get_active_prompt
from app.storage.file_manager import (
    get_project_folder_from_state,
    save_asset,
    sanitise_name,
)
from app.storage.mongo_session_store import mongo_session_store

logger = logging.getLogger(__name__)
router = APIRouter()

_agent_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ati-agent")
_session_upload_counts: dict[str, int] = {}
_session_upload_sizes: dict[str, int] = {}
_session_surf_counts: dict[str, int] = {}


def _run_agent_step_sync(session_id: str, user_message: str | None = None) -> dict:
    state = mongo_session_store.get_sync(session_id)
    if user_message is None:
        state = run_agent_step(state)
    else:
        state = process_message(state, user_message)
    mongo_session_store.update_sync(session_id, state)
    return state


async def _hydrate_memory(state: dict) -> None:
    user_id = state.get("user_id")
    tenant_id = state.get("tenant_id", "default")
    if user_id:
        ctx = await get_user_memory_context(user_id)
        state["user_memory_facts"] = ctx.get("facts", [])
        state["project_history"] = ctx.get("project_history", [])
        briefs = await Brief.find(Brief.user_id == user_id).sort(-Brief.created_at).limit(3).to_list()
        state["prior_briefs"] = [
            {"ref_id": b.ref_id, "client_name": b.client_name, "created_at": b.created_at.isoformat()}
            for b in briefs
        ]
    slm_template, prompt_version = await get_active_prompt("slm", tenant_id)
    state["slm_prompt_template"] = slm_template
    state["prompt_version"] = prompt_version
    state["learned_constraints"] = await build_learned_constraints_text(user_id, tenant_id)


async def _run_agent_step(session_id: str, user_message: str | None = None) -> dict:
    turn_start = time.perf_counter()
    state = await mongo_session_store.get(session_id)
    await _hydrate_memory(state)
    mongo_session_store.update_sync(session_id, state)

    loop = asyncio.get_running_loop()
    state = await asyncio.wait_for(
        loop.run_in_executor(_agent_executor, _run_agent_step_sync, session_id, user_message),
        timeout=90.0,
    )
    await mongo_session_store.update(session_id, state)

    if user_message and state.get("stage") in ("requirements", "clarify"):
        turn_count = state.get("requirements_turn_count", 0)
        if turn_count % 3 == 0:
            last_reply = state.get("pending_reply", "")
            asyncio.create_task(
                extract_and_store_facts(state.get("user_id"), user_message, last_reply)
            )

    elapsed = (time.perf_counter() - turn_start) * 1000
    metrics.record_turn(state.get("stage", "?"), elapsed, used_fallback=state.get("used_fallback", False))
    if user_message:
        rag_ctx = state.get("last_rag_context", "")
        rag_hash = hashlib.sha256(rag_ctx.encode()).hexdigest()[:16] if rag_ctx else ""
        turn_id = await record_turn(
            tenant_id=state.get("tenant_id", "default"),
            session_id=session_id,
            user_id=state.get("user_id"),
            stage=state.get("stage", ""),
            user_input=user_message,
            assistant_output=_reply_content(state),
            prompt_version=state.get("prompt_version", "v2.0"),
            rag_context_hash=rag_hash,
        )
        state["last_turn_id"] = turn_id
        await mongo_session_store.update(session_id, state)
    if state.get("done"):
        had_brief = bool(state.get("brief_id"))
        brief_id = await persist_brief_to_mongo(state)
        if brief_id:
            state["brief_id"] = brief_id
            await mongo_session_store.update(session_id, state)
        if not had_brief:
            await learn_from_completed_session(state)
            metrics.record_completion()
    return state


def _run_manual_brief_sync(session_id: str) -> dict:
    state = mongo_session_store.get_sync(session_id)
    state = request_manual_brief(state)
    mongo_session_store.update_sync(session_id, state)
    return state


async def _run_manual_brief(session_id: str) -> dict:
    pre_state = await mongo_session_store.get(session_id)
    had_brief = bool(pre_state.get("brief_id"))
    loop = asyncio.get_running_loop()
    state = await asyncio.wait_for(
        loop.run_in_executor(_agent_executor, _run_manual_brief_sync, session_id),
        timeout=90.0,
    )
    await mongo_session_store.update(session_id, state)

    if state.get("done"):
        brief_id = await persist_brief_to_mongo(state)
        if brief_id:
            state["brief_id"] = brief_id
            await mongo_session_store.update(session_id, state)
        if not had_brief:
            await learn_from_completed_session(state)
            metrics.record_completion()
    return state


def _reply_content(state: dict) -> str:
    if state.get("pending_reply"):
        return state["pending_reply"]
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "assistant" and msg.get("content"):
            return msg["content"]
    return "Hello! I'm the Client Onboarding Agent. How can I help with your project today?"


async def _send_assistant_reply(websocket: WebSocket, state: dict, *, include_history: bool = False, streamed: bool = False) -> None:
    content = _reply_content(state)
    stage = state.get("stage", "consent")
    brief_url = None
    if state.get("brief_id"):
        brief_url = f"/api/briefs/{state['brief_id']}/download"
    payload = {
        "type": "message",
        "role": "assistant",
        "content": content,
        "stage": stage,
        "done": state.get("done", False),
        "ref_id": state.get("ref_id"),
        "brief_id": state.get("brief_id"),
        "brief_download_url": brief_url,
        "requirements_complete": state.get("requirements_complete", False),
        "readiness_score": state.get("readiness_score", 0.0),
        "missing_fields": state.get("missing_fields", []),
        "auto_summarising": state.get("auto_summarising", False),
        "suggestions": get_suggestions(
            stage,
            state.get("client_name"),
            state.get("collected_requirements", {}).get("project_type"),
            state.get("requirements_complete", False),
            state.get("missing_fields", []),
        ),
        "consent_given": state.get("consent_given", False),
        "consent_required": not state.get("consent_given", False),
        "client_name": state.get("client_name"),
        "assets_count": len(state.get("assets", [])),
        "brief_version": state.get("brief_version", 1),
        "show_generate_brief": can_request_manual_brief(state),
        "show_brief_recap": state.get("awaiting_brief_confirm", False),
        "session_summary": state.get("session_summary", ""),
        "collected_requirements": state.get("collected_requirements", {}),
        "brief_updated": state.get("brief_update_pending", False),
        "streamed": streamed,
        "turn_id": state.get("last_turn_id"),
    }
    if include_history:
        payload["messages"] = state.get("messages", [])
    await websocket.send_json(payload)


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    user = await get_ws_user(websocket)
    if not user:
        return
    try:
        state = await mongo_session_store.get(session_id, str(user.id))
    except KeyError:
        await websocket.close(code=4404)
        return
    except PermissionError:
        await websocket.close(code=4403)
        return

    try:
        if not state.get("messages"):
            state = greeting_node(state)
            await mongo_session_store.update(session_id, state)
            logger.info("Initialized session %s awaiting modal consent", session_id)
            await _send_assistant_reply(websocket, state)
        else:
            logger.info("Syncing state to reconnected session %s", session_id)
            await _send_assistant_reply(websocket, state, include_history=True)
    except Exception:
        logger.exception("Error sending initial greeting for session %s", session_id)
        await websocket.send_json({
            "type": "message",
            "role": "assistant",
            "content": "Hello! I'm the Client Onboarding Agent. Let's begin with your privacy consent.",
            "stage": "consent",
            "suggestions": ["Tell me more about privacy", "What data do you collect?", "I'm ready to continue"],
            "consent_given": False,
        })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                payload = {"message": data}

            if payload.get("action") == "fill_field":
                field = payload.get("field")
                value = payload.get("value", "")
                if field and value:
                    state = await mongo_session_store.get(session_id, str(user.id))
                    collected = state.setdefault("collected_requirements", {})
                    collected[str(field)] = str(value)[:500]
                    await mongo_session_store.update(session_id, state)
                    await websocket.send_json({"type": "field_updated", "field": field, "value": value})
                continue

            if payload.get("action") == "consent":
                agreement = str(payload.get("agreement", ""))
                state = await mongo_session_store.get(session_id, str(user.id))
                if state.get("consent_given"):
                    await _send_assistant_reply(websocket, state, include_history=True)
                    continue
                if not is_modal_consent_phrase(agreement):
                    await websocket.send_json({
                        "type": "consent_error",
                        "message": 'Please type exactly "I agree" to continue.',
                        "consent_required": True,
                        "consent_given": False,
                    })
                    continue
                state = record_modal_consent(state)
                await mongo_session_store.update(session_id, state)
                await _send_assistant_reply(websocket, state, include_history=True)
                continue

            if payload.get("action") in ("feedback.thumbs", "feedback.step", "feedback.correction"):
                fb_state = await mongo_session_store.get(session_id, str(user.id))
                fb_type = payload.get("action", "").replace("feedback.", "")
                if fb_type == "thumbs":
                    fb_type = "thumbs_up" if payload.get("signal", 1) > 0 else "thumbs_down"
                signal = int(payload.get("signal", 0))
                comment = str(payload.get("comment", ""))
                if fb_type == "correction" and comment:
                    await store_correction_fact(str(user.id), comment)
                await ingest_feedback(
                    tenant_id=fb_state.get("tenant_id", "default"),
                    user_id=str(user.id),
                    feedback_type=fb_type,
                    signal=signal,
                    comment=comment,
                    session_id=session_id,
                    turn_id=payload.get("turn_id"),
                    task_type=task_type_for_stage(payload.get("stage", fb_state.get("stage", ""))),
                )
                await websocket.send_json({"type": "feedback_ack"})
                continue

            if payload.get("action") == "generate_brief":
                logger.info("Manual brief requested for session %s", session_id)
                try:
                    state = await _run_manual_brief(session_id)
                    await _send_assistant_reply(websocket, state)
                except asyncio.TimeoutError:
                    await websocket.send_json({
                        "type": "message",
                        "role": "assistant",
                        "content": "Sorry, brief generation took too long. Please try again.",
                        "stage": "error",
                        "suggestions": [],
                    })
                except Exception:
                    logger.exception("Error generating manual brief for session %s", session_id)
                    await websocket.send_json({
                        "type": "message",
                        "role": "assistant",
                        "content": "Sorry, something went wrong generating your brief. Please try again.",
                        "stage": "error",
                        "suggestions": [],
                    })
                continue

            user_message = payload.get("message", data)
            logger.info("Received message for session %s: %s", session_id, str(user_message)[:50])

            pre_state = await mongo_session_store.get(session_id, str(user.id))
            if not pre_state.get("consent_given"):
                await websocket.send_json({
                    "type": "consent_required",
                    "message": "Please complete the privacy consent dialog to continue.",
                    "consent_required": True,
                    "consent_given": False,
                })
                continue


            try:
                state = await _run_agent_step(session_id, user_message)
                content = _reply_content(state)
                if content and payload.get("stream", True) and state.get("stage") in ("requirements", "clarify", "identity"):
                    await websocket.send_json({"type": "stream_start"})
                    for i in range(0, len(content), 18):
                        await websocket.send_json({"type": "token", "content": content[i:i + 18]})
                        await asyncio.sleep(0.015)
                await _send_assistant_reply(websocket, state, streamed=bool(content))
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": "Sorry, that took too long. Please try again.",
                    "stage": "error",
                    "suggestions": [],
                })
            except Exception:
                logger.exception("Error processing message for session %s", session_id)
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": "Sorry, something went wrong. Please try again.",
                    "stage": "error",
                    "suggestions": [],
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session_id)


@router.post("/upload/{session_id}")
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    try:
        state = await mongo_session_store.get(session_id, str(user.id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not your session")

    if not state.get("consent_given"):
        raise HTTPException(status_code=403, detail="Consent required before uploading files")
    if not state.get("client_name"):
        raise HTTPException(status_code=400, detail="Client name required")
    if not is_supported(file.filename or ""):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_count = _session_upload_counts.get(session_id, 0)
    if file_count >= settings.MAX_FILES_PER_SESSION:
        raise HTTPException(status_code=400, detail=f"Maximum {settings.MAX_FILES_PER_SESSION} files per session")

    content = await file.read()
    total_size = _session_upload_sizes.get(session_id, 0) + len(content)
    if total_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Maximum {settings.MAX_UPLOAD_SIZE_MB} MB per session")

    from app.agent.nodes import _ensure_project_workspace

    _ensure_project_workspace(state)
    await mongo_session_store.update(session_id, state)
    client_folder = get_project_folder_from_state(state)
    saved_path = save_asset(client_folder, file.filename or "upload", content)

    try:
        extracted, proc_type = process_file(str(saved_path))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        extracted = f"[Processing error: {e}]"
        proc_type = "error"

    state["assets"].append(str(saved_path))
    state["asset_descriptions"][str(saved_path)] = extracted[:500]
    embed_text(
        extracted,
        f"project_{state.get('workspace_slug') or sanitise_name(state['client_name'])}",
        client_folder / "vectors",
        metadata={"source": str(saved_path), "type": proc_type},
    )
    state["file_context"] = f"File: {saved_path.name}\nType: {proc_type}\nContent: {extracted[:2000]}"
    await mongo_session_store.update(session_id, state)

    agent_message = None
    try:
        loop = asyncio.get_running_loop()
        def _clarify():
            s = mongo_session_store.get_sync(session_id)
            s = proactive_clarify_after_upload(s)
            mongo_session_store.update_sync(session_id, s)
            return s.get("pending_reply", "")
        agent_message = await asyncio.wait_for(loop.run_in_executor(_agent_executor, _clarify), timeout=90.0)
    except Exception:
        logger.exception("Proactive clarify after upload failed")

    _session_upload_counts[session_id] = file_count + 1
    _session_upload_sizes[session_id] = total_size

    return {
        "status": "saved",
        "filename": saved_path.name,
        "processing_type": proc_type,
        "description_preview": extracted[:200],
        "agent_message": agent_message,
    }


@router.post("/surf/{session_id}")
async def surf_url(
    session_id: str,
    body: SurfUrlRequest,
    user: User = Depends(get_current_user),
):
    from datetime import datetime, timezone

    from app.agent.nodes import _ensure_project_workspace
    from app.services.system_config_service import get_effective_settings
    from app.services.url_fetch_service import UrlFetchError, fetch_page_text

    try:
        state = await mongo_session_store.get(session_id, str(user.id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not your session")

    if not state.get("consent_given"):
        raise HTTPException(status_code=403, detail="Consent required before researching URLs")
    if not state.get("client_name"):
        raise HTTPException(status_code=400, detail="Client name required")

    tenant_id = state.get("tenant_id", user.tenant_id or "default")
    sys_cfg = await get_effective_settings(tenant_id)
    if not sys_cfg.get("surf_enabled", True):
        raise HTTPException(status_code=403, detail="URL research is disabled for this workspace")

    max_urls = int(sys_cfg.get("max_urls_per_session", 5))
    surfed = state.get("surfed_urls") or []
    url_count = _session_surf_counts.get(session_id, len(surfed))
    if url_count >= max_urls:
        raise HTTPException(status_code=400, detail=f"Maximum {max_urls} URLs per session")

    try:
        result = await fetch_page_text(body.url)
    except UrlFetchError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    _ensure_project_workspace(state)
    await mongo_session_store.update(session_id, state)
    client_folder = get_project_folder_from_state(state)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"surf_{timestamp}.txt"
    snapshot_body = f"URL: {result.final_url}\nTitle: {result.title}\n\n{result.text[:50000]}"
    saved_path = save_asset(client_folder, snapshot_name, snapshot_body.encode("utf-8"))

    collection = f"project_{state.get('workspace_slug') or sanitise_name(state['client_name'])}"
    embed_text(
        result.text[:20000],
        collection,
        client_folder / "vectors",
        metadata={"source": result.final_url, "type": "url_surf", "title": result.title},
    )

    if "surfed_urls" not in state or state["surfed_urls"] is None:
        state["surfed_urls"] = []
    state["surfed_urls"].append(result.final_url)
    state["assets"].append(str(saved_path))
    state["asset_descriptions"][str(saved_path)] = f"Reference URL: {result.title}"[:500]
    state["url_context"] = (
        f"URL: {result.final_url}\nTitle: {result.title}\nContent: {result.text[:2000]}"
    )
    await mongo_session_store.update(session_id, state)

    agent_message = None
    try:
        loop = asyncio.get_running_loop()

        def _clarify():
            s = mongo_session_store.get_sync(session_id)
            s = proactive_clarify_after_surf(s)
            mongo_session_store.update_sync(session_id, s)
            return s.get("pending_reply", "")

        agent_message = await asyncio.wait_for(loop.run_in_executor(_agent_executor, _clarify), timeout=90.0)
    except Exception:
        logger.exception("Proactive clarify after URL surf failed")

    _session_surf_counts[session_id] = url_count + 1

    return {
        "status": "saved",
        "url": result.final_url,
        "title": result.title,
        "description_preview": result.text[:200],
        "agent_message": agent_message,
    }
