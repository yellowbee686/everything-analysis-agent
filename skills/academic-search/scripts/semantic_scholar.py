#!/usr/bin/env python3
"""Small Semantic Scholar Graph API client for the academic-search skill."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_BASE_URL = "https://api.semanticscholar.org/graph/v1"
DEFAULT_SEARCH_FIELDS = (
    "paperId,title,abstract,year,venue,citationCount,"
    "influentialCitationCount,authors,externalIds,openAccessPdf,url"
)
DEFAULT_PAPER_FIELDS = (
    "paperId,title,abstract,year,venue,publicationDate,citationCount,"
    "influentialCitationCount,authors,externalIds,openAccessPdf,url,"
    "references,citations"
)
DEFAULT_AUTHOR_FIELDS = (
    "authorId,name,aliases,affiliations,homepage,paperCount,"
    "citationCount,hIndex,papers"
)

logger = logging.getLogger("semantic_scholar")


def _request_json(path: str, params: dict[str, str | int | None]) -> dict[str, Any]:
    """Request a Semantic Scholar endpoint and return decoded JSON."""
    clean_params = {key: value for key, value in params.items() if value is not None}
    query = urllib.parse.urlencode(clean_params)
    url = f"{API_BASE_URL}{path}"
    if query:
        url = f"{url}?{query}"

    headers = {"Accept": "application/json", "User-Agent": "academic-search-skill/1.0"}
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
            data = json.loads(payload)
            if isinstance(data, dict):
                return data
            return {"result": data}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error("Semantic Scholar HTTP error %s: %s", exc.code, body)
        return {"error": "http_error", "status": exc.code, "message": body, "url": url}
    except urllib.error.URLError as exc:
        logger.error("Semantic Scholar request failed: %s", exc)
        return {"error": "request_failed", "message": str(exc), "url": url}
    except json.JSONDecodeError as exc:
        logger.error("Semantic Scholar returned invalid JSON: %s", exc)
        return {"error": "invalid_json", "message": str(exc), "url": url}


def search_papers(args: argparse.Namespace) -> dict[str, Any]:
    """Search papers by query."""
    return _request_json(
        "/paper/search",
        {
            "query": args.query,
            "limit": args.limit,
            "offset": args.offset,
            "fields": args.fields,
            "year": args.year,
        },
    )


def get_paper(args: argparse.Namespace) -> dict[str, Any]:
    """Fetch paper details by Semantic Scholar paper ID."""
    paper_id = urllib.parse.quote(args.paper_id, safe="")
    return _request_json(f"/paper/{paper_id}", {"fields": args.fields})


def get_author(args: argparse.Namespace) -> dict[str, Any]:
    """Fetch author details by Semantic Scholar author ID."""
    author_id = urllib.parse.quote(args.author_id, safe="")
    return _request_json(f"/author/{author_id}", {"fields": args.fields})


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    parser = argparse.ArgumentParser(description="Query Semantic Scholar Graph API.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search-papers", help="Search papers.")
    search_parser.add_argument("query", help="Search query text.")
    search_parser.add_argument("--limit", type=int, default=5, help="Maximum papers to return.")
    search_parser.add_argument("--offset", type=int, default=0, help="Pagination offset.")
    search_parser.add_argument("--fields", default=DEFAULT_SEARCH_FIELDS, help="Comma-separated fields.")
    search_parser.add_argument("--year", default=None, help="Year filter, for example 2022- or 2020-2024.")
    search_parser.set_defaults(handler=search_papers)

    paper_parser = subparsers.add_parser("get-paper", help="Get one paper by ID.")
    paper_parser.add_argument("paper_id", help="Semantic Scholar paper ID, Corpus ID, DOI, or arXiv ID.")
    paper_parser.add_argument("--fields", default=DEFAULT_PAPER_FIELDS, help="Comma-separated fields.")
    paper_parser.set_defaults(handler=get_paper)

    author_parser = subparsers.add_parser("get-author", help="Get one author by ID.")
    author_parser.add_argument("author_id", help="Semantic Scholar author ID.")
    author_parser.add_argument("--fields", default=DEFAULT_AUTHOR_FIELDS, help="Comma-separated fields.")
    author_parser.set_defaults(handler=get_author)

    return parser


def main() -> int:
    """Run the CLI."""
    logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")
    parser = build_parser()
    args = parser.parse_args()

    result = args.handler(args)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
