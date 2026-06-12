from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth.dependencies import require_permission
from app.auth.tenant_context import get_user_tenant_id
from app.models.brief import Brief
from app.models.user import User
from app.services.docuseal_service import create_nda_submission

router = APIRouter(prefix="/api/admin/signatures", tags=["signatures"])


def _tenant_id(user: User, request: Request) -> str:
    return get_user_tenant_id(user, request)


@router.post("/briefs/{brief_id}/nda")
async def send_nda_for_brief(
    brief_id: str,
    request: Request,
    admin: User = Depends(require_permission("Pipeline", "Briefs", "update")),
):
    tenant_id = _tenant_id(admin, request)
    brief = await Brief.get(brief_id)
    if not brief or brief.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Brief not found")
    user = await User.get(brief.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Brief owner not found")
    ok, result = await create_nda_submission(
        tenant_id,
        submitter_email=user.email,
        submitter_name=user.full_name or brief.client_name,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=str(result))
    return {"success": True, "submission": result}
