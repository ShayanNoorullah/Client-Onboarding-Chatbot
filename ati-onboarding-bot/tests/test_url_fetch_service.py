import pytest

from app.services.url_fetch_service import (
    UrlFetchError,
    extract_urls_from_message,
    html_to_text,
    validate_url,
)


def test_extract_urls_from_message():
    text = "See https://example.com/page and http://foo.org"
    urls = extract_urls_from_message(text)
    assert "https://example.com/page" in urls
    assert "http://foo.org" in urls


def test_html_to_text_strips_scripts():
    html = """
    <html><head><title>Demo Site</title><script>alert(1)</script></head>
    <body><nav>Menu</nav><h1>Hello</h1><p>World</p></body></html>
    """
    title, text = html_to_text(html)
    assert title == "Demo Site"
    assert "Hello" in text
    assert "World" in text
    assert "alert" not in text
    assert "Menu" not in text


def test_validate_url_rejects_localhost():
    with pytest.raises(UrlFetchError):
        validate_url("https://localhost/test")


def test_validate_url_rejects_private_ip():
    with pytest.raises(UrlFetchError):
        validate_url("https://127.0.0.1/test")


def test_validate_url_rejects_file_scheme():
    with pytest.raises(UrlFetchError):
        validate_url("file:///etc/passwd")


def test_validate_url_normalizes_http_to_https(monkeypatch):
    monkeypatch.setattr(
        "app.services.url_fetch_service._assert_host_allowed",
        lambda _host: None,
    )
    assert validate_url("http://example.com/path") == "https://example.com/path"
