from docx import Document


def extract_docx_text(docx_path: str) -> str:
    """Extract all paragraph text from a DOCX file."""
    doc = Document(docx_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
