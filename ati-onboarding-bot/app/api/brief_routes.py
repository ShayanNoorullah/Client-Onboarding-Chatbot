from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.auth.dependencies import get_current_user, require_admin
from app.models.brief import Brief
from app.models.user import User

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
async def download_brief(brief_id: str, user: User = Depends(get_current_user)):
    brief = await _get_brief_for_user(brief_id, user)
    filename = f"{brief.ref_id}.md"
    return Response(
        content=brief.markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{brief_id}")
async def delete_brief(brief_id: str, user: User = Depends(get_current_user)):
    brief = await _get_brief_for_user(brief_id, user)
    await brief.delete()
    return {"status": "deleted", "id": brief_id}
