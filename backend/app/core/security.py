"""Input security, URL validation, and SSRF prevention guards.

Protects against:
- SSRF (Server-Side Request Forgery) by forbidding fetches to loopback,
  private/internal subnet ranges, link-local addresses, and non-HTTP protocols.
- Path traversal by stripping directory separators from upload filenames.
"""

import ipaddress
import logging
import os
import re
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Private and reserved network blocks to block for SSRF prevention
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # IPv4 loopback
    ipaddress.ip_network("10.0.0.0/8"),       # RFC 1918 private
    ipaddress.ip_network("172.16.0.0/12"),    # RFC 1918 private
    ipaddress.ip_network("192.168.0.0/16"),   # RFC 1918 private
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / cloud metadata (AWS, GCP, Azure)
    ipaddress.ip_network("0.0.0.0/8"),        # Current network
    ipaddress.ip_network("100.64.0.0/10"),    # Carrier-grade NAT
    ipaddress.ip_network("198.18.0.0/15"),    # Benchmark tests
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
]

_BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "::1", "metadata.google.internal"}


def is_safe_external_url(url: str) -> bool:
    """Validate whether an external URL is safe to fetch, blocking SSRF attempts.

    Returns False if URL is non-HTTP(S), targets a private/internal IP address,
    resolves to loopback/link-local metadata endpoints, or has invalid syntax.
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url.strip())
        if parsed.scheme.lower() not in ("http", "https"):
            return False

        hostname = (parsed.hostname or "").lower().strip()
        if not hostname or hostname in _BLOCKED_HOSTNAMES:
            return False

        # Attempt to parse direct IP address
        try:
            ip_obj = ipaddress.ip_address(hostname)
            for net in _BLOCKED_NETWORKS:
                if ip_obj in net:
                    return False
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                return False
        except ValueError:
            # Hostname is a domain name — resolve IP to verify target
            try:
                addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
                for _family, _, _, _, sockaddr in addr_info:
                    resolved_ip_str = sockaddr[0]
                    resolved_ip = ipaddress.ip_address(resolved_ip_str)
                    for net in _BLOCKED_NETWORKS:
                        if resolved_ip in net:
                            return False
                    if (
                        resolved_ip.is_private
                        or resolved_ip.is_loopback
                        or resolved_ip.is_link_local
                    ):
                        return False
            except socket.gaierror:
                # Unresolvable domains fail safely
                return False

        return True
    except Exception as exc:
        logger.warning("SSRF check error on %s: %s", url, exc)
        return False


def sanitize_filename(raw_name: str) -> str:
    """Strip path traversal elements and sanitize upload file name."""
    if not raw_name:
        return "uploaded_document"

    # Remove path directory separators
    name = os.path.basename(raw_name.replace("\\", "/"))
    # Remove null bytes and control chars
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    # Remove unsafe characters
    name = re.sub(r'[^a-zA-Z0-9._\-\s()]', "", name)
    # Prevent hidden files
    name = name.lstrip(".")
    if not name.strip():
        name = "uploaded_document"
    return name[:255]
