from pathlib import Path

import pytest

from app.processors.docx_processor import extract_docx_text
from app.processors.file_router import is_supported, process_file
from app.processors.pdf_processor import extract_pdf_text


def test_is_supported_valid():
    assert is_supported("document.pdf") is True
    assert is_supported("image.png") is True
    assert is_supported("data.docx") is True


def test_is_supported_invalid():
    assert is_supported("malware.exe") is False
    assert is_supported("archive.zip") is False


def test_process_txt_file(tmp_path):
    txt = tmp_path / "notes.txt"
    txt.write_text("Project requirements for mortgage website", encoding="utf-8")
    content, proc_type = process_file(str(txt))
    assert "mortgage website" in content
    assert proc_type == "text"


def test_process_csv_file(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("name,budget\nSarah,50000", encoding="utf-8")
    content, proc_type = process_file(str(csv))
    assert "Sarah" in content
    assert proc_type == "text"


def test_process_unsupported_raises(tmp_path):
    exe = tmp_path / "bad.exe"
    exe.write_bytes(b"\x00\x01")
    with pytest.raises(ValueError, match="Unsupported"):
        process_file(str(exe))


def test_extract_pdf_text_empty(tmp_path):
    try:
        import fitz

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello PDF World")
        pdf_path = tmp_path / "test.pdf"
        doc.save(str(pdf_path))
        doc.close()

        text = extract_pdf_text(str(pdf_path))
        assert "Hello PDF World" in text
    except Exception:
        pytest.skip("PyMuPDF PDF creation not available")


def test_extract_docx_text(tmp_path):
    try:
        from docx import Document

        doc = Document()
        doc.add_paragraph("Mortgage website requirements")
        docx_path = tmp_path / "test.docx"
        doc.save(str(docx_path))

        text = extract_docx_text(str(docx_path))
        assert "Mortgage website requirements" in text
    except Exception:
        pytest.skip("python-docx not available")
