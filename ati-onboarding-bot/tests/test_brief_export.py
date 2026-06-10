from pathlib import Path

from app.services.brief_export import markdown_to_pdf_bytes, markdown_to_plain_text

SAMPLE_MD = """# Project Brief

## Overview
Build a **web app** for onboarding.

- Feature one
- Feature two

| Field | Value |
|-------|-------|
| Name | Acme Corp |

## Next Steps
- [ ] Advisor review
- [ ] NDA signing (1–2 business days)
"""

SUMMARY_MD = Path(__file__).resolve().parents[1] / "client_data" / "ATI_Admin" / "2026-06-10_8f23391a" / "summary.md"


def test_markdown_to_plain_text_strips_formatting():
    text = markdown_to_plain_text(SAMPLE_MD)
    assert "PROJECT BRIEF" in text
    assert "**" not in text
    assert "Field  Value" in text or "Field" in text
    assert "[ ] Advisor review" in text


def test_markdown_to_pdf_bytes_returns_pdf():
    pdf = markdown_to_pdf_bytes(SAMPLE_MD)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 200


def test_pdf_renders_real_brief_without_raw_pipes():
    if not SUMMARY_MD.is_file():
        return
    markdown = SUMMARY_MD.read_text(encoding="utf-8")
    pdf = markdown_to_pdf_bytes(markdown)
    assert pdf[:4] == b"%PDF"
    doc = __import__("fitz").open(stream=pdf, filetype="pdf")
    text = "".join(page.get_text() for page in doc)
    doc.close()
    assert "| Field | Value |" not in text
    assert "Client Information" in text
    assert "ATI_Admin" in text or "ATIAdmin" in text.replace("_", "")
