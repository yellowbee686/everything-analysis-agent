---
name: qmd-analysis
description: Search the local analysis-md QMD index for Chinese linguistics and analysis markdown files, especially when results must use the analysis-md named index and include clickable local file links.
license: MIT
metadata:
  author: bytedance
  version: "0.1.0"
allowed-tools: Bash(qmd:*), Bash(python3:*), Bash(sqlite3:*), Bash(find:*), Bash(rg:*)
---

# QMD Analysis

Use this skill for searches over the local `analysis-md` QMD index.

Requires qmd CLI and the local `analysis-md` index at `~/.cache/qmd/analysis-md.sqlite`.

## Core Rules

- Always call qmd with `--index analysis-md`.
- The default qmd index `index` is not the analysis corpus and may be empty.
- Prefer BM25 for fast article listing:

```bash
qmd --index analysis-md search '全称量化' --json -n 20
```

- Use hybrid `query` only when semantic recall is needed; it may trigger model downloads or reranking delays.
- If using `query`, consider `--no-rerank` when speed matters.
- Treat qmd's `Updated: ... ago` as source-document freshness, not sqlite creation time.

## Local Corpus

- Collection: `analysis_md_files`
- Root: `/Users/bytedance/code/analysis-agent/data/analysis_md_files`
- Config: `~/.config/qmd/analysis-md.yml`
- Index: `~/.cache/qmd/analysis-md.sqlite`

## Clickable Links

Do not mechanically convert `qmd://analysis_md_files/...` to a local path. The qmd stored path can be normalized and may not match the current filename on disk.

When the user asks for clickable local links, use:

```bash
python3 skills/qmd-analysis/scripts/search_links.py '全称量化' -n 20
```

The script searches `analysis-md`, resolves qmd paths to real files under the corpus root, and emits Markdown links with absolute local paths.

## Relationship To The QMD Skill

This skill is a thin project-specific wrapper around the generic qmd skill. Use the generic qmd skill for command syntax and general QMD behavior. Use this skill whenever the task involves the `analysis-md` index, the `analysis_md_files` collection, or clickable links into the local analysis corpus.

Do not duplicate the full qmd manual here.
