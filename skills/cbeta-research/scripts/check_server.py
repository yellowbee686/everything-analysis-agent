#!/usr/bin/env python3
"""Check whether the CBETA MCP HTTP endpoint is reachable."""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_URL = "http://localhost:18765/mcp/"
logger = logging.getLogger("cbeta_mcp_check")


def _check_tcp(parsed_url: urllib.parse.ParseResult, timeout_s: float) -> dict[str, Any]:
    """Check whether the host and port accept TCP connections."""
    host = parsed_url.hostname or "localhost"
    port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return {"ok": True, "host": host, "port": port}
    except OSError as exc:
        logger.error("TCP check failed for %s:%s: %s", host, port, exc)
        return {"ok": False, "host": host, "port": port, "error": str(exc)}


def check_server(url: str, timeout_s: float) -> dict[str, Any]:
    """Check endpoint availability and return a JSON-serializable result."""
    parsed_url = urllib.parse.urlparse(url)
    tcp_result = _check_tcp(parsed_url, timeout_s)
    if not tcp_result["ok"]:
        return {
            "ok": False,
            "url": url,
            "reason": "tcp_unreachable",
            "detail": tcp_result,
        }

    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return {
                "ok": True,
                "url": url,
                "status": response.status,
                "reason": "http_reachable",
            }
    except urllib.error.HTTPError as exc:
        if exc.code < 500:
            return {
                "ok": True,
                "url": url,
                "status": exc.code,
                "reason": "endpoint_reachable_with_protocol_response",
            }
        body = exc.read().decode("utf-8", errors="replace")
        logger.error("HTTP check failed with %s: %s", exc.code, body)
        return {"ok": False, "url": url, "status": exc.code, "reason": "http_error", "message": body}
    except urllib.error.URLError as exc:
        logger.error("HTTP check failed: %s", exc)
        return {"ok": False, "url": url, "reason": "url_error", "message": str(exc)}


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    parser = argparse.ArgumentParser(description="Check CBETA MCP endpoint availability.")
    parser.add_argument("--url", default=DEFAULT_URL, help="MCP endpoint URL.")
    parser.add_argument("--timeout", type=float, default=3.0, help="Timeout in seconds.")
    return parser


def main() -> int:
    """Run the endpoint check."""
    logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args()
    result = check_server(args.url, args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
