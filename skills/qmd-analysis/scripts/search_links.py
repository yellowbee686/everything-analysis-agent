#!/usr/bin/env python3
"""Search the analysis-md QMD index and emit clickable local Markdown links."""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

INDEX_NAME = "analysis-md"
COLLECTION = "analysis_md_files"
ROOT = Path("/Users/bytedance/code/analysis-agent/data/analysis_md_files")


def normalize_key(value: str) -> str:
    """Normalize qmd and filesystem names for robust path matching."""
    value = value.casefold()
    value = re.sub(r"\.md$", "", value)
    return re.sub(r"[\s\-_—:：;；!?！？\"“”'‘’`*（）()\[\]【】《》<>.,，。、/\\\\]+", "", value)


def markdown_link(path: Path, title: str) -> str:
    """Return a Markdown link that works with special characters in local paths."""
    return f"[{title}](<{path}:1>)"


def run_qmd_search(query: str, limit: int) -> list[dict[str, Any]]:
    command = [
        "qmd",
        "--index",
        INDEX_NAME,
        "search",
        query,
        "--json",
        "-n",
        str(limit),
    ]
    proc = subprocess.run(command, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.error("qmd search failed: %s", proc.stderr.strip())
        return []

    output = proc.stdout.strip()
    start = output.find("[")
    if start < 0:
        logger.error("qmd search did not return JSON output")
        return []
    return json.loads(output[start:])


def build_file_index(root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in root.rglob("*.md"):
        relative = path.relative_to(root).as_posix()
        keys = {
            normalize_key(relative),
            normalize_key(path.name),
        }
        for key in keys:
            index.setdefault(key, []).append(path)
    return index


def qmd_uri_to_relative(uri: str) -> str:
    prefix = f"qmd://{COLLECTION}/"
    if not uri.startswith(prefix):
        return uri
    return uri.removeprefix(prefix)


def resolve_result_path(uri: str, file_index: dict[str, list[Path]]) -> Path | None:
    relative = qmd_uri_to_relative(uri)
    direct = ROOT / relative
    if direct.exists():
        return direct

    keys = [
        normalize_key(relative),
        normalize_key(Path(relative).name),
    ]
    for key in keys:
        matches = file_index.get(key, [])
        if matches:
            return sorted(matches, key=lambda path: ("/20251226/" in str(path), "pdf" in path.name, len(str(path))))[0]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="BM25 search query for qmd search")
    parser.add_argument("-n", "--limit", type=int, default=20, help="maximum qmd results")
    args = parser.parse_args()

    results = run_qmd_search(args.query, args.limit)
    if not results:
        return 1

    file_index = build_file_index(ROOT)
    for result in results:
        title = str(result.get("title") or result.get("file") or "Untitled")
        uri = str(result.get("file") or "")
        path = resolve_result_path(uri, file_index)
        score = result.get("score")
        score_text = f" score={score}" if score is not None else ""
        if path is None:
            print(f"- {title} ({uri}) [unresolved{score_text}]")
            continue
        print(f"- {markdown_link(path, title)}{score_text}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
