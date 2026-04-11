<!-- CompiledAt: 2026-04-10 22:30:16 -->
<!-- Source: web/20260409-185253-karpathy-llm-wiki.md -->
<!-- SourceHash: e1107ed4adf2516f27f3e33d0fcf4f75e0918048 -->
<!-- ExtractorVersion: raw_text_v1 -->
<!-- CompilePromptVersion: 2026-04-09-v1 -->

# Karpathy LLM Wiki

## Summary
- “Karpathy’s LLM Wiki” is described as a personal knowledge management workflow built from structured plain markdown files.
- The key idea is that the files are queried and maintained by an LLM/coding agent rather than primarily browsed by humans.
- Obsidian is commonly mentioned as a visual front-end for navigating the local files.
- The pattern is framed as a workflow, not a product: organize knowledge for model readability, then ask the model to answer, synthesize, and maintain the wiki.

## Key Claims
- The wiki is built on plain markdown files.
- It is intended to be queried by an LLM or agent such as Claude Code.
- The system can provide grounded answers from local notes instead of the general internet.
- Obsidian is useful for visualization and graph navigation of the local knowledge base.
- Some sources claim the approach works well without embeddings or a vector database at Karpathy’s described scale, relying instead on summary files.
- A recurring theme is that consistency and maintenance matter more than raw retrieval.
- One source claims the LLM can read new material, update relevant pages, detect contradictions, and create concept pages as needed; this is presented as a proposed or aspirational workflow, not directly verified here.

## Concepts And Entities
- Andrej Karpathy
  - Associated with the “LLM wiki” idea.
- LLM wiki
  - A local, structured knowledge base designed for LLM consumption.
- Plain markdown
  - Preferred file format because it is portable and LLM-readable.
- Claude Code
  - Mentioned as a coding agent that can query and manage the wiki.
- Obsidian
  - Used as a local visualization and graph interface.
- Summary files
  - Mentioned as a way to support indexing without embeddings/vector DB at small scale.
- Tags, folders, linting
  - Suggested mechanisms to keep the wiki consistent as it grows.
- Digital exhaust
  - A phrase used to describe scattered personal files and notes that can be consolidated.
- Cross-linked pages
  - A structural feature emphasized in the sources.
- RAG
  - Mentioned in contrast to the wiki pattern in some discussions.
- Live web data / search-extract pipelines
  - Presented in one source as an extension of the wiki idea.

## Contradictions Or Tensions
- Human navigation vs. model navigation
  - The wiki is optimized for AI use, which may differ from what is easiest for humans.
- Personal use vs. team/student access
  - One source notes the pattern is useful personally but may not solve access needs for students or broader audiences.
- No embeddings/vector DB vs. richer retrieval stacks
  - Some discussion suggests the system can work without vector search at modest scale, but this may not generalize.
- Static knowledge base vs. continuously updated knowledge
  - Sources differ in emphasis: some focus on a local personal wiki, others on a system that continuously compiles and reconciles new information.
- Simple setup vs. long-term maintenance
  - The initial setup is described as easy by some sources, but others stress that consistency, contradiction handling, and scale become hard over time.

## Open Questions
- What exact structure Karpathy originally recommended is not fully specified in the source capture.
- How much of the described behavior is Karpathy’s own guidance versus later interpretations or products built around the idea is unclear.
- At what scale the no-embedding, summary-file approach stops working is not specified.
- Whether contradiction detection and automatic page updates are part of the original concept or later extensions is uncertain.
- How best to adapt the pattern for shared/team use remains unresolved in the source set.

## Practical Notes
- Use plain markdown files as the storage format.
- Keep the data local and file-based if you want portability and future-proofing.
- Use Obsidian if you want a visual graph for browsing the knowledge base.
- Add consistent tags and concise summaries to improve query quality.
- Plan for maintenance: linting, tagging, and folder structure help prevent drift.
- The approach is most directly suited to personal knowledge workflows; if others need access, a separate publishing or UI layer may be required.
- Treat this as a workflow pattern that can be adapted, not as a fixed product.
