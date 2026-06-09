import shutil
from pathlib import Path

import pytest

from app.storage.file_manager import (
    create_client_workspace,
    delete_client_data,
    sanitise_name,
    save_asset,
)


@pytest.fixture
def tmp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.STORAGE_ROOT", tmp_path)
    yield tmp_path
    if tmp_path.exists():
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sanitise_name_basic():
    assert sanitise_name("Sarah Johnson") == "Sarah_Johnson"


def test_sanitise_name_special_chars():
    assert sanitise_name("John@Doe!#$") == "JohnDoe"


def test_sanitise_name_unicode():
    result = sanitise_name("José García")
    assert "Jos" in result or "Garca" in result


def test_sanitise_name_long():
    long_name = "A" * 100
    assert len(sanitise_name(long_name)) == 64


def test_sanitise_name_spaces():
    assert sanitise_name("  Multiple   Spaces  ") == "Multiple_Spaces"


def test_create_client_workspace(tmp_storage):
    folder = create_client_workspace("Test Client")
    assert folder.exists()
    assert (folder / "assets").exists()
    assert (folder / "vectors").exists()


def test_create_client_workspace_idempotent(tmp_storage):
    folder1 = create_client_workspace("Test Client")
    folder2 = create_client_workspace("Test Client")
    assert folder1 == folder2


def test_save_asset(tmp_storage):
    folder = create_client_workspace("Asset Test")
    path = save_asset(folder, "test.txt", b"hello world")
    assert path.exists()
    assert path.read_bytes() == b"hello world"


def test_delete_client_data(tmp_storage):
    create_client_workspace("Delete Me")
    assert delete_client_data("Delete Me") is True
    assert not (tmp_storage / "Delete_Me").exists()


def test_delete_nonexistent_client(tmp_storage):
    assert delete_client_data("Nobody") is False
