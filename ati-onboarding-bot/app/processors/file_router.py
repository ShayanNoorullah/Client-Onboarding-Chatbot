from pathlib import Path

from app.config import settings
from app.processors.docx_processor import extract_docx_text
from app.processors.image_processor import describe_image
from app.processors.pdf_processor import extract_pdf_text

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
TEXT_EXTENSIONS = {".txt", ".csv"}


def is_supported(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in settings.SUPPORTED_EXTENSIONS


def process_file(file_path: str) -> tuple[str, str]:
    """
    Process a file and return (extracted_text_or_description, processing_type).
    Raises ValueError for unsupported formats.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in IMAGE_EXTENSIONS:
        description = describe_image(file_path)
        return description, "image"

    if ext == ".pdf":
        text = extract_pdf_text(file_path)
        return text, "pdf"

    if ext == ".docx":
        text = extract_docx_text(file_path)
        return text, "docx"

    if ext in TEXT_EXTENSIONS:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text, "text"

    if ext == ".xlsx":
        try:
            import openpyxl

            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            rows = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_text = " | ".join(str(c) for c in row if c is not None)
                    if row_text.strip():
                        rows.append(row_text)
            wb.close()
            return "\n".join(rows), "xlsx"
        except Exception as e:
            return f"[Could not parse XLSX: {e}]", "xlsx"

    raise ValueError(f"Unsupported file type: {ext}")
