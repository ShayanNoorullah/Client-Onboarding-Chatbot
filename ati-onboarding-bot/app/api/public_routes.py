import re
from pathlib import Path

from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/api/public", tags=["public"])

_PRIVACY_PATH = settings.ATI_KB_ROOT / "privacy_policy.txt"


def _parse_privacy_sections(text: str) -> list[dict]:
    """Split privacy_policy.txt into titled sections."""
    lines = text.strip().splitlines()
    sections: list[dict] = []
    current_title = ""
    current_body: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\d+\.\s", stripped):
            if current_title or current_body:
                sections.append({
                    "title": current_title,
                    "body": "\n".join(current_body).strip(),
                })
            current_title = stripped
            current_body = []
        elif not sections and not current_title and not re.match(r"^\d+\.", stripped):
            if stripped.upper().startswith("AWESOME TECHNOLOGIES"):
                continue
            if "Contact:" in stripped or "Address:" in stripped:
                continue
            if not current_title:
                current_title = stripped
            else:
                current_body.append(stripped)
        else:
            current_body.append(stripped)

    if current_title or current_body:
        sections.append({
            "title": current_title,
            "body": "\n".join(current_body).strip(),
        })

    return [s for s in sections if s.get("title")]


@router.get("/privacy")
async def get_privacy_policy():
    if not _PRIVACY_PATH.exists():
        return {
            "title": "Privacy Policy",
            "contact": {
                "email": settings.ATI_SUPPORT_EMAIL,
                "phone": settings.ATI_PHONE,
                "address": "4400 State Highway 121 Ste 374, Lewisville, TX 75056",
            },
            "sections": [],
        }

    raw = _PRIVACY_PATH.read_text(encoding="utf-8")
    lines = raw.strip().splitlines()
    title = lines[0].strip() if lines else "Privacy Policy"

    return {
        "title": title,
        "contact": {
            "email": settings.ATI_SUPPORT_EMAIL,
            "phone": settings.ATI_PHONE,
            "address": "4400 State Highway 121 Ste 374, Lewisville, TX 75056",
        },
        "sections": _parse_privacy_sections(raw),
    }
