# Academic Search Query Workflows

## Default Fields

Use compact fields for initial search:

```text
paperId,title,abstract,year,venue,citationCount,influentialCitationCount,authors,externalIds,openAccessPdf,url
```

Use expanded fields for paper detail:

```text
paperId,title,abstract,year,venue,publicationDate,citationCount,influentialCitationCount,authors,externalIds,openAccessPdf,url,references,citations
```

Use author fields only when needed:

```text
authorId,name,aliases,affiliations,homepage,paperCount,citationCount,hIndex,papers
```

## Search Strategy

- Start with the user's exact terminology.
- If results are sparse, try one broader synonym query and one method-specific query.
- For recent surveys, add a year filter such as `--year 2022-`.
- For foundational work, remove the year filter and rank by citation count plus title relevance.
- Prefer open-access URLs for follow-up reading, but do not exclude closed papers unless the user asks.

## Filtering and Deduplication

- Deduplicate by `paperId` first, then by normalized title.
- Treat arXiv, DOI, ACL, PubMed, and Corpus ID as external identifiers for disambiguation.
- Down-rank papers with missing abstracts unless title, venue, or citation count makes them clearly relevant.
- For author queries, verify the author ID before attributing papers to a person with a common name.

## Synthesis

- Separate "what the API returned" from analytical conclusions.
- Include paper title, year, venue, citation count, and URL or paper ID in source-backed summaries.
- For literature reviews, group papers by method, dataset/domain, or chronology depending on the user's goal.
- If the API returns an error or rate limit, state it and avoid filling gaps from memory.
