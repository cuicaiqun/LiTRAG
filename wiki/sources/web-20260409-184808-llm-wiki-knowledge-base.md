<!-- CompiledAt: 2026-04-10 22:30:07 -->
<!-- Source: web/20260409-184808-llm-wiki-knowledge-base.md -->
<!-- SourceHash: 4bd7e9298baacc84329d13ff6bce050431c4ef0d -->
<!-- ExtractorVersion: raw_text_v1 -->
<!-- CompilePromptVersion: 2026-04-09-v1 -->

# LLM Wiki Knowledge Base

## Summary
- The source describes an LLM knowledge base as a structured information system used to reduce hallucinations and stale answers by giving the model domain-specific context at runtime.
- It emphasizes that the main challenge is often not retrieval architecture itself, but governance of the underlying data.
- A notable example is a “wiki-first” approach: keep knowledge in markdown/wiki form, maintain an index page, and have the LLM read the index first, then drill into relevant pages.
- The source contrasts lightweight personal/small-team setups with enterprise environments, which have larger scale, access controls, and continuous change.

## Key Claims
- An LLM knowledge base can reduce hallucinations and answer staleness without retraining the model.
- Core types mentioned:
  - vector store / RAG
  - knowledge graph / GraphRAG
  - structured wiki
- The primary failure mode is often not the retrieval method, but:
  - ungoverned source data
  - stale data
  - undocumented data
- Retrieval architecture is described as a relatively well-understood engineering problem.
- Data governance upstream of the knowledge base is portrayed as the more neglected and failure-prone area.
- For personal knowledge bases, a markdown-based wiki may work without a vector database if the content stays under roughly 100K tokens.
- A wiki-style workflow can scale “surprisingly well” at moderate scale, around:
  - ~100 sources
  - hundreds of pages
- The described wiki pattern avoids the need for embedding-based RAG infrastructure in some cases.

## Concepts And Entities
- **LLM knowledge base**: external data store queried at runtime for domain-specific, current context.
- **Hallucination reduction**: one of the main benefits claimed for LLM knowledge bases.
- **Answer staleness**: outdated responses are another problem the knowledge base is meant to address.
- **Vector store / RAG**: one possible architecture for retrieval.
- **Knowledge graph / GraphRAG**: another architecture option.
- **Structured wiki**: a wiki organized for model consumption.
- **Governance layer**: metadata, policy, and control layer over the source data.
- **Active metadata catalog**: Atlan’s framing for a governed knowledge substrate.
- **index.md**: in the wiki approach, a content-oriented catalog listing all pages with:
  - a link
  - a one-line summary
  - optional metadata such as date or source count
- **Ingest process**: the wiki index is updated on every ingest.
- **Query process**: the LLM reads the index first, then relevant pages.
- **Personal knowledge base**: individual use case where simple markdown/context-window reading may be enough.
- **Enterprise knowledge estate**: large, changing, access-controlled content environment.

## Contradictions Or Tensions
- There is a tension between:
  - **simple wiki/markdown approaches** for individuals or small teams
  - **more governed architectures** for enterprise-scale, access-controlled, fast-changing data
- Another tension is between focusing on:
  - **retrieval architecture** as the main design problem
  - **data governance** as the more important but under-addressed failure point
- The source suggests the wiki approach can replace embedding-based RAG in moderate-scale settings, but implies that this does not generalize cleanly to larger enterprise contexts.

## Open Questions
- What exact governance mechanisms are required for enterprise-scale LLM knowledge bases? The source mentions the need, but does not specify them in detail.
- How should the threshold between “small enough for markdown/wiki” and “needs richer architecture” be determined beyond the rough 100K-token guidance?
- How robust is the wiki/index-first approach across different query types and content churn rates?
- What benchmarks best compare wiki-based systems with vector stores or knowledge graphs in practice?

## Practical Notes
- A practical wiki workflow described in the source is:
  - keep pages in markdown
  - maintain an `index.md`
  - list each page with a short summary and metadata
  - update the index whenever new content is ingested
  - have the LLM consult the index before deeper lookup
- This approach may be effective for:
  - competitive analysis
  - due diligence
  - trip planning
  - course notes
  - hobby deep-dives
- The source frames this as useful when knowledge is accumulated over time and should be organized rather than scattered.
- For smaller, stable, well-curated collections, avoiding a vector database may be a valid simplification.
