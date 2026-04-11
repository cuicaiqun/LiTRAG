# Knowledge Map

## Core Themes

### 1) Wiki/knowledge-base workflows for LLMs
- Several pages describe an “LLM Wiki” approach built from plain markdown files.
- The shared idea is to organize knowledge so an LLM or coding agent can read, query, update, and cross-reference it.
- This approach is framed as a workflow or pattern, not a product.
- A common design is: keep a readable markdown corpus, maintain an index, and let the model drill down into relevant pages.

### 2) Knowledge management as a response to retrieval limitations
- The LLM Wiki / knowledge-base pages emphasize reducing hallucinations and stale answers by giving the model structured, domain-specific context.
- Traditional RAG is contrasted as repeatedly retrieving fragments at question time, while the wiki approach emphasizes prior compilation and understanding.
- A recurring theme is that governance and maintenance of the knowledge base may matter more than retrieval architecture alone.

### 3) Structured factual reference pages
- The Chinese regex slide is a compact reference page listing symbols and their meanings.
- The Solo Leveling pages are structured summaries of a media franchise, including author, publication history, adaptations, plot setup, and sequel/continuation notes.
- These pages fit the wiki pattern by packaging knowledge into stable, queryable summaries.

### 4) Mapping and association between entities
- The ROBMS page appears to encode a correspondence between two lists: historical/fictional Chinese figures on the left and numbered weapons/items/abilities on the right.
- The visual design suggests cross-linking or classification rather than isolated facts.

### 5) Configuration and infrastructure around the knowledge system
- The API configuration notes show model/provider setup, embedding, reranking, and external search/API settings.
- This suggests the knowledge workflow is supported by an underlying tool stack, not just content pages.

---

## Important Connections

### LLM Wiki pages connect to the repository’s own structure
- The wiki description pages are directly relevant to the way the overall corpus is organized: local markdown files, index pages, cross-reference behavior, and agent maintenance.
- They provide a conceptual model for why the other pages exist as discrete summaries.

### The regex page fits the “wiki-first” knowledge-base pattern
- It is a concise, self-contained teaching note with explicit symbol-to-meaning mappings.
- This is the kind of canonical knowledge that benefits from stable markdown storage and quick retrieval.

### The Solo Leveling pages show how a topic can be normalized across variants
- Multiple summaries cover the same work with overlapping but not identical details.
- Together they illustrate how a knowledge base can aggregate multilingual names, publication timelines, adaptations, and sequel status.

### The API configuration page supports the LLM wiki workflow
- Model, embedding, and reranker settings imply the system is prepared for document understanding, retrieval, and synthesis.
- The presence of an external search/API key suggests integration with broader retrieval or enrichment tools.

### The ROBMS page suggests cross-document entity mapping
- The connected two-table layout indicates relationships are being encoded visually.
- In a wiki environment, such mappings could become explicit links, pages, or annotations.

---

## Contradictions / Conflicts

### “通配符” vs. regex terminology
- The regex slide is titled “常用通配符” but the content is actually standard regex metacharacters.
- This is a terminology mismatch rather than a factual contradiction.

### Different levels of completeness across source summaries
- The ROBMS page is truncated in the provided text, so the full set of entries and mappings is not visible.
- The API configuration notes are also truncated before listing all fields.
- The Solo Leveling pages differ in detail, with one mentioning broad media/franchise facts and another adding sequel timing and character/setting specifics.

### Variation in naming and transliteration
- Solo Leveling appears under Chinese title, Korean title, English title, and Japanese title.
- The main character also appears under multiple name forms, which can look inconsistent if not normalized.

---

## Missing Evidence

### For the regex slide
- No surrounding lecture context is provided, so it is unclear whether the title’s “通配符” is meant loosely or pedagogically.
- There is no example usage showing how the symbols behave in actual matching.

### For the ROBMS page
- The right-side list is incomplete in the extracted summary.
- The nature of the mapping is unclear: whether it is semantic, game-related, story-related, or something else.
- No explanation is given for why `关羽` is highlighted.

### For the API configuration page
- The summary is cut off before all configuration fields are shown.
- The purpose of each setting in the larger system is not explained.
- The exact role of the exposed secrets is not described beyond being secret-like and sensitive.

### For the LLM Wiki / knowledge-base pages
- The summaries describe the pattern, but not a full implementation guide.
- There is limited evidence about how index pages are structured, how conflicts are resolved, or how updates are validated.

### For Solo Leveling
- The pages mention multiple media adaptations and sequel plans, but do not fully reconcile release timelines across regions.
- The summary references “some pages with incomplete coverage,” so the exact completeness of franchise data is not guaranteed.

---

## Suggested Next Questions

1. How does the repository want to distinguish “通配符” from regex metacharacters in teaching pages?
2. What is the full mapping shown in the ROBMS table, and what do the colored lines represent?
3. How should incomplete source summaries be merged when the same topic appears in multiple pages?
4. What is the intended index structure for this LLM Wiki-style knowledge base?
5. Which model, embedding, and reranking components are actually active in the API configuration, and how are they used together?
6. Should multilingual aliases like Solo Leveling / 我独自升级 / 나 혼자만 레벨업 be normalized onto a single canonical page?
7. What validation or maintenance process is used to keep wiki pages current and consistent?
8. Are there explicit links between conceptual pages like the LLM Wiki notes and example content pages like regex or Solo Leveling?
