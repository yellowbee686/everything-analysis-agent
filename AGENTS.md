# AGENTS.md

## System Rules

- Read this file and the relevant skill or submodule `AGENTS.md` before making changes.
- Communicate with users in Chinese.
- Write code, comments, docstrings, and command-facing text in English unless a domain term requires Chinese.
- Python code must include type annotations.
- Prefer readable, pythonic code.
- Follow fail-fast behavior. When compatibility handling is needed, log with `logger.error` and return a clear error result instead of raising from user-facing helpers.
- Prefer built-in collection types such as `list` and `dict` over `List` and `Dict`.

## Repository Purpose

This repository stores analysis-agent assets such as skills, plugins, and MCP integrations.

## Docs

- Research and design notes live under `docs/`.
- When the target reader is Chinese, `docs/` research notes may be written in Chinese.
- Include the investigation date and source references for comparative or external research notes.
- QMD setup and usage notes live in `docs/qmd_usage.md`.

## Skills

- Skills live under `skills/<skill-name>/`.
- Each skill must include `SKILL.md` with `name` and `description` frontmatter.
- Keep `SKILL.md` concise. Put detailed workflows, tool maps, and setup notes in `references/`.
- Put deterministic helper commands in `scripts/`.
- Validate changed skills with:

```bash
python3 /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/<skill-name>
```

If the default `python3` does not have `PyYAML`, use any project virtual environment that provides `yaml`.

## CBETA MCP Submodule

- `mcp_servers/CbetaMCP` is a git submodule pinned to a known commit.
- Do not commit virtual environments, caches, logs, or generated Python bytecode from the submodule.
- The default local MCP endpoint is `http://localhost:18765/mcp/`.
- Start the CBETA MCP server only when a live CBETA query requires it. Check the endpoint first, then start it on demand.
