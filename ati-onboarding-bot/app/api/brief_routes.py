from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.responses import Response

from app.auth.dependencies import get_current_user, require_admin
from app.models.brief import Brief
from app.models.brief_feedback import BriefFeedback
from app.models.user import User
from app.services.brief_export import markdown_to_pdf_bytes, markdown_to_plain_text

router = APIRouter(prefix="/api/briefs", tags=["briefs"])


async def _get_brief_for_user(brief_id: str, user: User, admin: bool = False) -> Brief:
    brief = await Brief.get(brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    if not admin and brief.user_id != str(user.id):
        raise HTTPException(status_code=403, detail="Not your brief")
    return brief


@router.get("")
async def list_briefs(user: User = Depends(get_current_user)):
    briefs = await Brief.find(Brief.user_id == str(user.id)).sort(-Brief.created_at).to_list()
    return {"briefs": [b.to_public() for b in briefs]}


@router.get("/{brief_id}")
async def get_brief(brief_id: str, user: User = Depends(get_current_user)):
    brief = await _get_brief_for_user(brief_id, user)
    data = brief.to_public()
    data["markdown"] = brief.markdown
    return data


@router.get("/{brief_id}/download")
async def download_brief(
    brief_id: str,
    user: User = Depends(get_current_user),
    format: str = Query(default="md", alias="format"),
):
    brief = await _get_brief_for_user(brief_id, user)
    fmt = format.lower().strip()
    if fmt not in ("md", "txt", "pdf"):
        raise HTTPException(status_code=400, detail="Format must be md, txt, or pdf")

    if fmt == "md":
        filename = f"{brief.ref_id}.md"
        return Response(
            content=brief.markdown,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    if fmt == "txt":
        filename = f"{brief.ref_id}.txt"
        content = markdown_to_plain_text(brief.markdown)
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    filename = f"{brief.ref_id}.pdf"
    pdf_bytes = markdown_to_pdf_bytes(brief.markdown)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )




class BriefFeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""


@router.post("/{brief_id}/feedback")
async def submit_brief_feedback(brief_id: str, body: BriefFeedbackRequest, user: User = Depends(get_current_user)):
    brief = await _get_brief_for_user(brief_id, user)
    from app.services.feedback_service import ingest_feedback

    signal = 1 if body.rating >= 4 else -1 if body.rating <= 2 else 0
    existing = await BriefFeedback.find_one(BriefFeedback.brief_id == brief_id, BriefFeedback.user_id == str(user.id))
    if existing:
        existing.rating = body.rating
        existing.comment = body.comment
        await existing.save()
        fb = existing
    else:
        fb = BriefFeedback(
            user_id=str(user.id),
            brief_id=brief_id,
            session_id=brief.session_id,
            rating=body.rating,
            comment=body.comment,
        )
        await fb.insert()

    await ingest_feedback(
        tenant_id=user.tenant_id or "default",
        user_id=str(user.id),
        feedback_type="brief_rating",
        signal=signal,
        comment=body.comment,
        session_id=brief.session_id,
        brief_id=brief_id,
        task_type="brief_generation",
        context={"rating": body.rating},
    )
    if signal < 0 and brief.session_id:
        from app.services.pattern_quality_service import deprecate_patterns_for_session

        await deprecate_patterns_for_session(brief.session_id)

    return {"feedback": fb.to_public()}

@router.delete("/{brief_id}")
async def delete_brief(brief_id: str, user: User = Depends(get_current_user)):
    brief = await _get_brief_for_user(brief_id, user)
    await brief.delete()
    return {"status": "deleted", "id": brief_id}
