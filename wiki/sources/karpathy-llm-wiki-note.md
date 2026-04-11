<!-- CompiledAt: 2026-04-10 22:29:39 -->
<!-- Source: karpathy-llm-wiki-note.md -->
<!-- SourceHash: d99fa732165934593ead9014dc3aedca20f1c13c -->
<!-- ExtractorVersion: raw_text_v1 -->
<!-- CompilePromptVersion: 2026-04-09-v1 -->

# LLM Wiki vs Traditional RAG

## Summary
- The source contrasts traditional RAG with an “LLM Wiki” approach.
- Traditional RAG is described as repeatedly retrieving fragments from source material at question time.
- LLM Wiki emphasizes compiling and understanding information first, then answering from structured knowledge.
- Strong question-answering outputs can be fed back into the knowledge base, creating continuous accumulation.
- The source also highlights practical use cases, risks, and maintenance practices.

## Key Claims
- Traditional RAG is more like “reopening the book” each time and focusing on finding relevant fragments.
- LLM Wiki prioritizes compilation and comprehension before answering.
- Good answers can be reused to enrich the knowledge base.
- This creates a knowledge system that can grow over time.
- If the compilation step hallucinates, errors may spread and become amplified.
- Long-term knowledge base maintenance requires expiration handling and version management.

## Concepts And Entities
- **Traditional RAG**
  - Retrieval-centered approach.
  - Emphasis on finding source snippets at query time.
- **LLM Wiki**
  - A compiled, structured knowledge layer.
  - Answers are based on organized understanding rather than only on direct retrieval.
- **Raw source / raw knowledge**
  - Should retain original text and source metadata.
- **Knowledge base**
  - Can be enriched by high-quality answers.
  - Needs governance for stale content and versions.
- **Personal knowledge management**
  - Listed as a suitable scenario.
- **Learning notes**
  - Listed as a suitable scenario.
- **Small-scale customer support knowledge base**
  - Suggested for tens to hundreds of documents.

## Contradictions Or Tensions
- There is a tension between:
  - **Retrieval fidelity** in traditional RAG, and
  - **Compiled abstraction** in LLM Wiki.
- LLM Wiki may improve coherence and reuse, but it increases the risk that one hallucinated compilation error gets propagated.
- The source implies a tradeoff between convenience/structure and the need for stronger governance.
- It is not fully specified how to decide when a compiled wiki entry should override or supplement raw source material.

## Open Questions
- How should compilation quality be validated before a wiki page is trusted?
- What specific rules should govern “expiration management” and version control?
- How should conflicting source documents be represented in the wiki?
- When should the system prefer raw retrieval over compiled wiki knowledge?
- What criteria determine whether a generated answer is good enough to be fed back into the knowledge base?

## Practical Notes
- Keep raw source text and source metadata together in the raw layer.
- Force every wiki page to include a “contradictions / uncertainty” section.
- Record the referenced page(s) for every answer to support accountability and later iteration.
- The approach appears best suited to:
  - personal knowledge management,
  - study notes,
  - small customer-support knowledge bases with roughly dozens to hundreds of documents.
