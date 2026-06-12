from pathlib import Path
import re

ADMIN_DIR = Path(__file__).resolve().parent.parent / "static" / "admin"
TITLES = {
    "dashboard.html": "Dashboard",
    "sessions.html": "Sessions",
    "briefs.html": "Briefs",
    "pipeline-types.html": "Project Types",
    "config-system.html": "System Configuration",
    "config-smtp.html": "SMTP",
    "config-email-templates.html": "Email Templates",
    "config-followup.html": "Follow-up Timing",
    "settings-actions.html": "Application Action",
    "settings-modules.html": "Application Module",
    "settings-pages.html": "Application Page",
    "settings-roles.html": "Role",
    "settings-users.html": "User",
    "reports.html": "Reports",
    "health.html": "Health",
    "users.html": "Users",
}

for name, title in TITLES.items():
    path = ADMIN_DIR / name
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(
        r"<title>[^<]*</title>",
        f"<title>{title} — Client Onboarding Agent Admin</title>",
        text,
        count=1,
    )
    text = re.sub(
        r'(<link href="/static/css/admin-v2.css" rel="stylesheet">\s*)+',
        '  <link href="/static/css/admin-v2.css" rel="stylesheet">\n',
        text,
    )
    path.write_text(text, encoding="utf-8")
    print(name)
