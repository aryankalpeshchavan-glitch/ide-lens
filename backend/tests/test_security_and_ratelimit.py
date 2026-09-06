"""Tests for input security, SSRF validation, filename sanitization, and API rate limiting."""

import pytest
from fastapi import HTTPException

from app.core.rate_limit import RateLimiter
from app.core.security import is_safe_external_url, sanitize_filename


def test_ssrf_validator_blocks_internal_and_cloud_metadata():
    """Verify loopback, private RFC1918, link-local, and cloud metadata targets are rejected."""
    # Loopback
    assert is_safe_external_url("http://127.0.0.1/admin") is False
    assert is_safe_external_url("http://localhost:8000/metrics") is False
    assert is_safe_external_url("http://[::1]/secret") is False

    # Private network subnets
    assert is_safe_external_url("http://10.0.1.5/api") is False
    assert is_safe_external_url("http://192.168.1.1/router") is False
    assert is_safe_external_url("http://172.16.0.2/internal") is False

    # Cloud metadata service (AWS/GCP/Azure link-local)
    assert is_safe_external_url("http://169.254.169.254/latest/meta-data/") is False

    # Non-HTTP protocols
    assert is_safe_external_url("file:///etc/passwd") is False
    assert is_safe_external_url("ftp://internal.vault/keys") is False
    assert is_safe_external_url("gopher://localhost:70") is False

    # Legitimate external public endpoints
    assert is_safe_external_url("https://arxiv.org/abs/2312.00752") is True
    assert is_safe_external_url("https://api.semanticscholar.org/graph/v1/paper/search") is True
    assert is_safe_external_url("https://github.com/torvalds/linux") is True


def test_filename_sanitization_prevents_path_traversal():
    """Verify directory traversal and unsafe characters are stripped from filenames."""
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\Windows\\System32\\calc.exe") == "calc.exe"
    assert sanitize_filename("research_paper (v2).pdf") == "research_paper (v2).pdf"
    assert sanitize_filename(".hidden_file.txt") == "hidden_file.txt"
    assert sanitize_filename("") == "uploaded_document"


def test_rate_limiter_triggers_429_when_exceeded():
    """Verify sliding-window rate limiter raises HTTP 429 once request limit is reached."""
    limiter = RateLimiter(requests_per_minute=3, scope="test_scope")

    class DummyClient:
        host = "198.51.100.42"

    class DummyRequest:
        headers = {"X-Forwarded-For": "198.51.100.42"}
        client = DummyClient()

    req = DummyRequest()

    # 3 allowed requests
    limiter(req)
    limiter(req)
    limiter(req)

    # 4th request must raise 429
    with pytest.raises(HTTPException) as exc_info:
        limiter(req)

    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail
    assert "Retry-After" in exc_info.value.headers
