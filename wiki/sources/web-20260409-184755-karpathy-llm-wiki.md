<!-- CompiledAt: 2026-04-10 22:29:57 -->
<!-- Source: web/20260409-184755-karpathy-llm-wiki.md -->
<!-- SourceHash: 87d96ac52413a403e2e9247b53cc277196be03fe -->
<!-- ExtractorVersion: raw_text_v1 -->
<!-- CompilePromptVersion: 2026-04-09-v1 -->

# Karpathy LLM Wiki
## Summary
- Andrej Karpathy is described as proposing an “LLM wiki” for personal knowledge management.
- The core pattern is a directory of structured markdown files that LLMs can read, query, update, and cross-reference.
- The source emphasizes that this is a workflow/pattern rather than a product.
- The files are intended to stay local and readable by both humans and LLMs, with agents like Claude Code used to interact with them.

## Key Claims
- A useful knowledge base for LLMs can be built from plain markdown files.
- The LLM can “own” the wiki layer by creating pages, updating them when new sources arrive, maintaining cross-references, and keeping consistency.
- Structured markdown is preferred because it is portable, future-proof, and natively readable by LLMs.
- The setup can be queried directly by coding agents such as Claude Code without copy-pasting content into chat.
- A summary line and consistent tags on each note are said to improve query quality.
- Obsidian is presented as a strong front-end for managing the files while keeping data local.
- For team-facing or scaled use cases, a no-code wrapper like MindStudio is mentioned as an alternative way to expose the same pattern through a UI.

## Concepts And Entities
- **Andrej Karpathy**: Identified as the source of the “LLM wiki” idea in the captured material.
- **LLM wiki**: A personal knowledge management system built from structured markdown files and queried by an LLM.
- **Markdown files**: The main storage format; emphasized as plain, portable, and readable by models.
- **Claude Code**: Mentioned as an example of a coding agent that can query the folder directly.
- **Obsidian**: Mentioned as a local file-based front-end for working with the notes.
- **MindStudio**: Mentioned as a possible UI layer for team-facing or scaled deployments.
- **Idea file / gist**: Referred to as a follow-up document that lays out the architecture, philosophy, and tooling behind the concept.
- **RAG**: Mentioned as a comparison point, with the source framing the wiki approach as preferable in some workflows.

## Contradictions Or Tensions
- The source presents the wiki approach as a replacement or improvement over typical RAG/document workflows, but it does not provide technical benchmarking or limits.
- It implies that the LLM can maintain consistency and cross-references, but does not explain failure modes or oversight requirements.
- It emphasizes local, file-based control, while also mentioning team-scale or no-code wrappers, which may introduce a tension between simplicity and shared access.
- Some details appear to come from secondary articles and summaries rather than a primary source, so exact wording or attribution may be uncertain.

## Open Questions
- What is the exact original structure of Karpathy’s idea file or gist?
- Which markdown conventions are required, if any, for the wiki pages to work well?
- How much of the page creation and maintenance should be automated versus manually reviewed?
- What are the practical limits of using this approach instead of RAG for larger corpora?
- How should conflicts between pages or sources be resolved when the LLM updates the wiki?

## Practical Notes
- Keep the knowledge base in plain markdown to maximize portability and LLM readability.
- Use consistent headings, summaries, and tags to help retrieval.
- A local-first tool such as Obsidian can be used to browse and edit the files.
- A coding agent like Claude Code can be pointed at the folder to answer questions and help maintain the wiki.
- For more structured sharing or collaboration, a wrapper/UI layer may be useful, though the source treats this as secondary.
