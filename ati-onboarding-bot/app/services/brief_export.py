"""Brief export helpers for txt and pdf formats."""

import re

import fitz

PAGE_W = 595
PAGE_H = 842
MARGIN = 50
CONTENT_W = PAGE_W - 2 * MARGIN

_FONT = "helv"
_FONT_BOLD = "hebo"


def _normalize_chars(text: str) -> str:
    return (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2022", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )


def _strip_inline_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return _normalize_chars(text.strip())


def _is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.endswith("|")


def _is_table_separator(line: str) -> bool:
    s = line.strip()
    if not _is_table_row(s):
        return False
    inner = s.strip("|").replace("|", "").strip()
    return bool(inner) and all(c in "-: " for c in inner)


def _parse_table_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


class _BriefPdfWriter:
    def __init__(self) -> None:
        self.doc = fitz.open()
        self.page = self.doc.new_page(width=PAGE_W, height=PAGE_H)
        self.y = float(MARGIN)

    def _ensure_space(self, height: float) -> None:
        if self.y + height > PAGE_H - MARGIN:
            self.page = self.doc.new_page(width=PAGE_W, height=PAGE_H)
            self.y = float(MARGIN)

    def _wrap_lines(self, text: str, fontsize: float, max_width: float, font: str) -> list[str]:
        words = text.split()
        if not words:
            return []
        lines: list[str] = []
        current: list[str] = []
        for word in words:
            trial = " ".join(current + [word])
            if fitz.get_text_length(trial, fontname=font, fontsize=fontsize) > max_width and current:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return lines

    def _write_textbox(
        self,
        text: str,
        *,
        fontsize: float = 11,
        bold: bool = False,
        indent: float = 0,
        color: tuple[float, float, float] = (0, 0, 0),
    ) -> None:
        if not text:
            return
        font = _FONT_BOLD if bold else _FONT
        max_width = CONTENT_W - indent
        line_height = fontsize * 1.4
        x0 = MARGIN + indent

        for line in self._wrap_lines(text, fontsize, max_width, font):
            self._ensure_space(line_height + 2)
            self.page.insert_text(
                (x0, self.y + fontsize),
                line,
                fontsize=fontsize,
                fontname=font,
                color=color,
            )
            self.y += line_height
        self.y += 4

    def _write_heading(self, text: str, level: int) -> None:
        sizes = {1: 18, 2: 14, 3: 12}
        size = sizes.get(level, 12)
        self._ensure_space(size + 16)
        self.y += 10 if level <= 2 else 6
        self._write_textbox(_strip_inline_markdown(text), fontsize=size, bold=True)

    def _write_paragraph(self, text: str, *, bold: bool = False, indent: float = 0) -> None:
        self._ensure_space(18)
        self._write_textbox(_strip_inline_markdown(text), fontsize=11, bold=bold, indent=indent)

    def _write_bullet(self, text: str, *, checkbox: bool = False) -> None:
        self._ensure_space(16)
        prefix = "[ ] " if checkbox else "- "
        self._write_textbox(prefix + _strip_inline_markdown(text), fontsize=11, indent=12)

    def _draw_rule(self) -> None:
        self._ensure_space(14)
        self.y += 4
        self.page.draw_line(
            fitz.Point(MARGIN, self.y),
            fitz.Point(MARGIN + CONTENT_W, self.y),
            color=(0.75, 0.75, 0.75),
            width=0.5,
        )
        self.y += 10

    def _render_table(self, table_lines: list[str]) -> None:
        rows: list[list[str]] = []
        for line in table_lines:
            if _is_table_separator(line):
                continue
            rows.append([_strip_inline_markdown(c) for c in _parse_table_row(line)])
        if not rows:
            return

        col_count = max(len(r) for r in rows)
        for row in rows:
            while len(row) < col_count:
                row.append("")

        col_widths = [CONTENT_W / col_count] * col_count
        pad_x = 6
        pad_y = 6
        font_size = 10
        row_h = font_size + pad_y * 2 + 4

        self._ensure_space(row_h * len(rows) + 8)
        self.y += 4

        for r_idx, row in enumerate(rows):
            self._ensure_space(row_h + 4)
            x = float(MARGIN)
            y_top = self.y
            font = _FONT_BOLD if r_idx == 0 else _FONT
            for c_idx, cell in enumerate(row):
                w = col_widths[c_idx]
                rect = fitz.Rect(x, y_top, x + w, y_top + row_h)
                fill = (0.95, 0.95, 0.95) if r_idx == 0 else (1, 1, 1)
                self.page.draw_rect(rect, color=(0.8, 0.8, 0.8), fill=fill, width=0.5)
                self.page.insert_text(
                    (x + pad_x, y_top + pad_y + font_size),
                    cell,
                    fontsize=font_size,
                    fontname=font,
                    color=(0, 0, 0),
                )
                x += w
            self.y += row_h

        self.y += 8

    def render(self, markdown: str) -> bytes:
        lines = markdown.replace("\r\n", "\n").split("\n")
        i = 0
        table_buf: list[str] = []

        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()

            if _is_table_row(stripped):
                table_buf.append(stripped)
                i += 1
                continue
            if table_buf:
                self._render_table(table_buf)
                table_buf = []

            if not stripped:
                self.y += 6
                i += 1
                continue

            if stripped in ("---", "***", "___"):
                self._draw_rule()
                i += 1
                continue

            if stripped.startswith("#"):
                level = len(stripped) - len(stripped.lstrip("#"))
                heading = stripped[level:].strip()
                self._write_heading(heading, min(level, 3))
                i += 1
                continue

            checkbox_match = re.match(r"^[-*]\s+\[\s*([xX ]?)\s*\]\s*(.+)$", stripped)
            if checkbox_match:
                self._write_bullet(checkbox_match.group(2), checkbox=True)
                i += 1
                continue

            if re.match(r"^[-*]\s+", stripped):
                self._write_bullet(re.sub(r"^[-*]\s+", "", stripped))
                i += 1
                continue

            if stripped.startswith("**") and "**" in stripped[2:]:
                self._write_paragraph(stripped, bold=False)
                i += 1
                continue

            if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
                self._write_paragraph(stripped[1:-1])
                i += 1
                continue

            self._write_paragraph(stripped)
            i += 1

        if table_buf:
            self._render_table(table_buf)

        pdf_bytes = self.doc.tobytes()
        self.doc.close()
        return pdf_bytes


def markdown_to_plain_text(markdown: str) -> str:
    text = markdown.replace("\r\n", "\n")
    out: list[str] = []
    table_buf: list[str] = []

    def flush_table() -> None:
        nonlocal table_buf
        if not table_buf:
            return
        for line in table_buf:
            if _is_table_separator(line):
                continue
            cells = _parse_table_row(line)
            out.append("  ".join(_strip_inline_markdown(c) for c in cells))
        table_buf = []
        out.append("")

    for line in text.split("\n"):
        stripped = line.strip()
        if _is_table_row(stripped):
            table_buf.append(stripped)
            continue
        flush_table()

        if not stripped:
            out.append("")
            continue
        if stripped in ("---", "***", "___"):
            out.append("-" * 40)
            continue
        if stripped.startswith("#"):
            heading = re.sub(r"^#+\s*", "", stripped)
            out.append(heading.upper())
            out.append("")
            continue
        checkbox_match = re.match(r"^[-*]\s+\[\s*([xX ]?)\s*\]\s*(.+)$", stripped)
        if checkbox_match:
            out.append(f"  [ ] {checkbox_match.group(2)}")
            continue
        if stripped.startswith(("- ", "* ")):
            out.append(f"  - {stripped[2:].strip()}")
            continue
        out.append(_strip_inline_markdown(stripped))

    flush_table()
    return "\n".join(out).strip() + "\n"


def markdown_to_pdf_bytes(markdown: str, title: str | None = None) -> bytes:
    content = markdown.strip()
    if title and not content.lstrip().startswith("#"):
        content = f"# {title}\n\n{content}"
    return _BriefPdfWriter().render(content)
