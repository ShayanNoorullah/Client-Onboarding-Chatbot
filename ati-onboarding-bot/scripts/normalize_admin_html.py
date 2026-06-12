"""Normalize admin HTML pages: titles, CSS, and script includes."""
from pathlib import Path

ADMIN_DIR = Path(__file__).resolve().parent.parent / "static" / "admin"
V = "3.8.0"

CSS_BLOCK = """  <link href="/static/css/app.css" rel="stylesheet">
  <link href="/static/css/theme.css" rel="stylesheet">
  <link href="/static/css/theme-presets.css" rel="stylesheet">
  <link href="/static/css/settings.css" rel="stylesheet">
  <link href="/static/css/admin-v2.css" rel="stylesheet">"""

COMMON_SCRIPTS = f"""  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  <script src="/static/js/api.js?v={V}"></script>
  <script src="/static/js/auth.js?v={V}"></script>
  <script src="/static/js/theme.js?v={V}"></script>
  <script src="/static/js/settings.js?v={V}"></script>
  <script src="/static/js/admin-utils.js?v={V}"></script>
  <script src="/static/js/admin-layout.js?v={V}"></script>
  <script src="/static/js/admin-shell.js?v={V}"></script>"""


def normalize(path: Path) -> None:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    if "_layout.html" in path.name:
        return

    # Fix title suffix
    import re
    text = re.sub(
        r"<title>([^<]+)</title>",
        lambda m: f"<title>{m.group(1).split('—')[0].split('|')[0].split('Client Onboarding Agent')[0].strip()} — Client Onboarding Agent Admin</title>"
        if "Client Onboarding Agent" not in m.group(1)
        else f"<title>{re.sub(r'[—|].*', '', m.group(1)).strip()} — Client Onboarding Agent Admin</title>",
        text,
        count=1,
    )

    # Ensure theme-bootstrap
    if "theme-bootstrap.js" not in text:
        text = text.replace("<head>", f'<head>\n  <script src="/static/js/theme-bootstrap.js?v={V}"></script>', 1)

    # Normalize CSS: remove admin.css, transitions.css duplicates; ensure standard block
    for old in ["admin.css", "transitions.css"]:
        text = re.sub(rf'\s*<link href="/static/css/{old}" rel="stylesheet">\n?', "", text)

    if "theme.css" not in text:
        if 'href="/static/css/app.css"' in text:
            text = text.replace(
                '<link href="/static/css/app.css" rel="stylesheet">',
                CSS_BLOCK,
                1,
            )
        elif "admin-v2.css" in text:
            text = text.replace(
                '<link href="/static/css/admin-v2.css" rel="stylesheet">',
                CSS_BLOCK,
                1,
            )

    # Find page-specific script (last script before </body>)
    page_script_match = re.search(r'(<script src="/static/js/[^"]+\.js[^"]*"></script>)\s*</body>', text)
    page_script = page_script_match.group(1) if page_script_match else ""
    if page_script and "admin-shell.js" in page_script:
        page_script = ""

    # Remove old script blocks before </body>
    text = re.sub(
        r'\s*<script src="https://cdn\.jsdelivr\.net/npm/bootstrap[^<]+</script>.*?(\s*<script src="/static/js/[^"]+\.js[^"]*"></script>)*\s*</body>',
        "\n" + COMMON_SCRIPTS + ("\n  " + page_script if page_script and "admin-shell" not in page_script else "") + "\n</body>",
        text,
        flags=re.DOTALL,
    )

  # Fix double titles
    text = re.sub(r" — Client Onboarding Agent Admin — Client Onboarding Agent Admin", " — Client Onboarding Agent Admin", text)

    path.write_text(text, encoding="utf-8")
    print(f"Updated {path.name}")


for html in sorted(ADMIN_DIR.glob("*.html")):
    normalize(html)
