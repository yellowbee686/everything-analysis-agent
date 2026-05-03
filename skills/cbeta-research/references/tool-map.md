# CBETA MCP Tool Map

## Search Tools

- `cbeta_all_in_one`: Best first tool for broad keyword search. Returns KWIC snippets and optional facets.
- `cbeta_search_sc`: Use when the user gives simplified Chinese; it handles simplified/traditional conversion.
- `cbeta_fulltext_search`: Use for plain full-text search when KWIC/facets are not needed.
- `extended_search`: Use for boolean or proximity queries such as `般若 AND 波羅蜜` or `"般若" NEAR/5 "波羅蜜"`.
- `search_cbeta_notes`: Search annotations, variants, notes, and collation content.
- `cbeta_facet_query`: Aggregate by `canon`, `category`, `dynasty`, `creator`, or `work`.
- `synonym_search`: Explore related CBETA terms before reformulating a query.
- `cbeta_similar_search`: Use for similarity search after an initial relevant phrase is known.

## Catalog and Metadata Tools

- `search_title`: Search scripture titles.
- `search_cbeta_texts`: Search catalog entries by keyword or volume token.
- `get_cbeta_catalog`: Browse catalog hierarchy.
- `search_buddhist_canons_by_vol`: Search by canon and volume range.
- `search_works_by_translator`: Search by translator or creator. Prefer `creator_id` when known.
- `search_cbeta_by_dynasty`: Search by dynasty or year range.
- `get_cbeta_work_info`: Fetch canonical metadata for one work ID such as `T0001`.
- `get_cbeta_toc`: Fetch table of contents for one work.

## Source Text Tools

- `get_cbeta_lines`: Retrieve exact text by linehead or linehead range. Use for final citation whenever possible.
- `cbeta_goto`: Build navigation URL by linehead or structured coordinates.
- `get_juan_html`: Retrieve one fascicle's HTML content.
- `cbeta_kwic_search`: Search inside one work and juan for local context.

## Recommended Flows

- Keyword discovery: `cbeta_all_in_one` with `facet=1`, then `get_cbeta_lines` for representative lineheads.
- Simplified Chinese query: `cbeta_search_sc`, then retry promising terms with traditional Chinese in `cbeta_all_in_one`.
- Scripture title lookup: `search_title`, then `get_cbeta_work_info`, then `get_cbeta_toc`.
- Translator research: `search_works_by_translator`, then group results by dynasty/category and verify key works with `get_cbeta_work_info`.
- Close reading: `get_cbeta_toc`, then `get_juan_html` or `get_cbeta_lines`, then `cbeta_goto` for user-facing navigation.

## Citation Fields

Prefer citations in this order:

```text
title, work, juan, linehead, canon, vol, page/col/line, cbeta_goto URL
```

Preserve returned source text exactly unless asked to normalize or translate.
