from app.storage.file_manager import make_workspace_slug, sanitise_name


def test_make_workspace_slug():
    slug = make_workspace_slug("abc12345-6789-0000-0000-000000000000")
    assert slug.endswith("_abc12345")
    assert len(slug.split("_")) == 2


def test_sanitise_name():
    assert sanitise_name("Shayan Noorullah") == "Shayan_Noorullah"
