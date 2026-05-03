---
name: academic-search
description: Search academic literature with Semantic Scholar and synthesize paper, author, citation, and related-work findings. Use when Codex needs to find papers, compare research directions, inspect paper metadata, gather citation context, or produce source-backed academic summaries without depending on project-specific agent runtimes.
---

# Academic Search

## Overview

Use Semantic Scholar as the default live academic search source. Prefer the bundled `scripts/semantic_scholar.py` CLI for deterministic JSON retrieval, then synthesize results in the user's requested language.

## Workflow

1. Clarify the research target only when the query is underspecified. Otherwise search directly.
2. Run `scripts/semantic_scholar.py search-papers "<query>" --limit <n>` with focused fields.
3. Inspect titles, abstracts, venue, year, citation count, influential citation count, authors, and open-access URLs.
4. Fetch paper details for high-value candidates with `get-paper` when abstracts, references, citations, or external IDs are needed.
5. Fetch author details with `get-author` only when the user asks about a person, publication record, or author disambiguation.
6. Summarize with explicit uncertainty. Do not invent claims beyond returned metadata.

## Commands

On Windows, follow the current agent environment. Use WSL2 if the agent is already in WSL2; otherwise native Windows Python is fine for this skill.

Search papers:

```bash
python3 skills/academic-search/scripts/semantic_scholar.py search-papers "retrieval augmented generation" --limit 10
```

Get paper details:

```bash
python3 skills/academic-search/scripts/semantic_scholar.py get-paper CorpusID:208324896
```

Get author information:

```bash
python3 skills/academic-search/scripts/semantic_scholar.py get-author 1741102
```

## References

- Read `references/query-workflows.md` for field presets, filtering, deduplication, and synthesis guidance.
- Use `SEMANTIC_SCHOLAR_API_KEY` when available. The script also works without it, subject to public rate limits.

## Output Rules

- Cite paper titles, years, venues, and paper IDs or URLs when available.
- Separate search results from interpretation.
- Mention API or rate-limit failures plainly and include the failed command when useful.
- Prefer compact tables for paper comparisons and concise bullets for literature summaries.
