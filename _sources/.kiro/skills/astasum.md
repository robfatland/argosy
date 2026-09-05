---
inclusion: manual
---

# astasum — Academic Paper Search and Summary

When this skill is invoked, search for academic papers matching the user's query
using web search against Semantic Scholar, then return results in compressed format.

## Behavior

1. Parse the user's query for:
   - **Search terms** (the topic/keywords)
   - **Count** — look for "top N" or "N results" in the prompt. Default: 5 results.
   - **Recency** — if the user says "recent" or specifies a year range, filter accordingly.

2. Search using web search tools targeting Semantic Scholar / Google Scholar.
   Retrieve: title, authors, year, abstract summary, citation count if available, URL.

3. Return results in this compressed format (one entry per paper):

```
**[N]** FirstAuthor et al. (Year). "Title." [Citations: X]
   Summary: <one sentence distilling the abstract>
   Link: <URL>
```

4. If the user says "top 1" → return exactly 1 result.
   If "top 3" → return 3. Default without specification: 5.

5. After presenting results, ask: "Want more detail on any of these?"

## Example invocations

- `#astasum internal wave detection moored profiler` → 5 results
- `#astasum top 1 Savitzky-Golay oceanographic profile smoothing` → 1 result
- `#astasum top 3 recent methane seep monitoring cabled observatory` → 3 results, prefer recent

## Output style

Keep it compact. No lengthy preambles. Results immediately after the search.
If no results found, say so and suggest query refinements.
