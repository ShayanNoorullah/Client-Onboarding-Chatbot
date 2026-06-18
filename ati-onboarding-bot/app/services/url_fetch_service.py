"""SSRF-safe HTTPS fetch and HTML text extraction for agent URL research."""

from __future__ import annotations

import ipaddress
import logging
import re
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
FETCH_TIMEOUT_SEC = 10.0
USER_AGENT = "ATI-OnboardingBot/1.0 (+https://awesometechinc.com)"


@dataclass
class SurfResult:
    title: str
    text: str
    final_url: str
    char_count: int


class UrlFetchError(ValueError):
    pass


def extract_urls_from_message(text: str) -> list[str]:
    found = URL_PATTERN.findall(text or "")
    return list(dict.fromkeys(found))


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _resolve_host_ips(hostname: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UrlFetchError(f"Could not resolve host: {hostname}") from exc
    ips: list[str] = []
    for info in infos:
        sockaddr = info[4]
        if sockaddr:
            ips.append(sockaddr[0])
    return ips


def _assert_host_allowed(hostname: str) -> None:
    host = (hostname or "").strip().lower().rstrip(".")
    if not host:
        raise UrlFetchError("URL host is required")
    if host in ("localhost", "metadata.google.internal"):
        raise UrlFetchError("Host not allowed")
    if host.endswith(".local") or host.endswith(".internal"):
        raise UrlFetchError("Host not allowed")

    for ip_str in _resolve_host_ips(host):
        if _is_blocked_ip(ip_str):
            raise UrlFetchError("URL points to a private or reserved address")


def validate_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        raise UrlFetchError("URL is required")

    parsed = urlparse(raw)
    if parsed.scheme not in ("https",):
        if parsed.scheme in ("http",):
            parsed = parsed._replace(scheme="https")
        else:
            raise UrlFetchError("Only HTTPS URLs are allowed")

    if not parsed.netloc:
        raise UrlFetchError("Invalid URL")

    _assert_host_allowed(parsed.hostname or "")

    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    normalized = f"https://{parsed.netloc}{path}"
    return normalized


def html_to_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
        tag.decompose()
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    text = soup.get_text("\n", strip=True)
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return title, "\n".join(lines)


async def fetch_page_text(url: str) -> SurfResult:
    safe_url = validate_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=FETCH_TIMEOUT_SEC,
        max_redirects=5,
    ) as client:
        try:
            response = await client.get(safe_url, headers=headers)
        except httpx.HTTPError as exc:
            raise UrlFetchError(f"Could not fetch URL: {exc}") from exc

        final_host = urlparse(str(response.url)).hostname or ""
        _assert_host_allowed(final_host)

        if response.status_code >= 400:
            raise UrlFetchError(f"URL returned HTTP {response.status_code}")

        content = response.content
        if len(content) > MAX_RESPONSE_BYTES:
            content = content[:MAX_RESPONSE_BYTES]

        content_type = (response.headers.get("content-type") or "").lower()
        if "html" not in content_type and "text" not in content_type:
            raise UrlFetchError("URL did not return HTML or text content")

        charset = response.encoding or "utf-8"
        try:
            html = content.decode(charset, errors="replace")
        except LookupError:
            html = content.decode("utf-8", errors="replace")

    title, text = html_to_text(html)
    if not text:
        raise UrlFetchError("No readable text found on page")

    return SurfResult(
        title=title or safe_url,
        text=text[:50000],
        final_url=str(response.url),
        char_count=len(text),
    )
