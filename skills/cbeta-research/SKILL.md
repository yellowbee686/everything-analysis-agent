---
name: cbeta-research
description: Use the CBETA MCP server for Chinese Buddhist scripture search, catalog lookup, metadata retrieval, KWIC inspection, and source-text citation. Use when Codex needs live CBETA queries, Buddhist canon text lookup, work/juan/linehead citation, translator or dynasty searches, or CBETA MCP tool guidance.
---

# CBETA Research

## Overview

Use the `mcp_servers/CbetaMCP` submodule as the live tool server. This skill provides startup policy, tool selection, and citation workflows; it does not duplicate the MCP tool implementations.

## Startup Policy

Do not start the MCP server when the skill is loaded. Start it only when the user task needs a live CBETA query.

1. Check the endpoint first:

```bash
python3 skills/cbeta-research/scripts/check_server.py --url http://localhost:18765/mcp/
```

2. If unavailable, start on demand:

```bash
skills/cbeta-research/scripts/start_server.sh
```

When running inside an agent shell that cleans up background processes, keep the server in a long-running foreground session:

```bash
CBETA_MCP_FOREGROUND=1 skills/cbeta-research/scripts/start_server.sh
```

3. Re-run the check. If it still fails, report dependency, port, or server-log diagnostics.

The default MCP endpoint is `http://localhost:18765/mcp/`.

## Windows Preference

On Windows, prefer running CBETA MCP commands inside WSL2. Fall back to PowerShell only when WSL2 is unavailable or the user explicitly asks for native Windows execution.

- If the agent is already running in WSL2, use the normal Linux commands above.
- If the agent is running in native Windows PowerShell or CMD and WSL2 is available, run Linux commands through `wsl.exe -- bash -lc`.
- If WSL2 is unavailable, use `scripts\start_server.ps1` from PowerShell.
- Convert Windows paths such as `C:\Users\name\repo` to WSL paths such as `/mnt/c/Users/name/repo` before calling Linux scripts.

Example from native Windows:

```powershell
wsl.exe -- bash -lc 'cd /mnt/c/path/to/everything-analysis-agent && skills/cbeta-research/scripts/start_server.sh'
```

Fallback from native PowerShell:

```powershell
.\skills\cbeta-research\scripts\start_server.ps1
```

## Query Workflow

1. Use `references/tool-map.md` to choose the smallest useful tool set.
2. For broad discovery, start with `cbeta_all_in_one` or `cbeta_search_sc`.
3. For exact Buddhist canon metadata, use catalog or work tools before content retrieval.
4. For final answers, prefer source-backed snippets from `get_cbeta_lines`, `cbeta_kwic_search`, or `get_juan_html`.
5. Include `work`, `title`, `juan`, and `linehead` when available. Preserve traditional Chinese source text unless the user asks for simplified Chinese.

## References

- Read `references/tool-map.md` for tool categories, common parameter shapes, and recommended flows.
- Read `references/setup.md` for submodule initialization, dependency installation, endpoint configuration, and troubleshooting.

## Output Rules

- Distinguish search hits from verified source text.
- Show CBETA identifiers in citations: `work`, `title`, `juan`, `linehead`, and URL from `cbeta_goto` when available.
- Report MCP startup failures with the check/start command and relevant log path.
