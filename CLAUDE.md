# LLM Wiki Project Rules

## Mission

Build and maintain a knowledge base that favors compiled understanding over raw retrieval.

## Directories

- `raw/`: unstructured source materials (notes, papers, articles, transcripts, screenshots converted to text).
- `wiki/`: compiled knowledge pages generated and refined over time.
- `outputs/`: Q&A artifacts from user queries.

## Principles

1. Compile first, answer second.
2. Prefer wiki pages over raw text when answering.
3. Track contradictions, uncertainty, and source coverage.
4. Treat strong answers as reusable assets and promote them into `wiki/qa/`.
5. Keep references explicit (which wiki pages informed each answer).

## Compilation Contract

When compiling from `raw/` into `wiki/sources/`, each page should include:

- concise summary
- key claims/facts
- concepts and entities
- contradictions or ambiguities
- open questions
- practical takeaways

## Answering Contract

When answering a question:

1. Retrieve relevant pages from `wiki/`.
2. Answer only from compiled knowledge.
3. If evidence is missing, say so clearly.
4. Cite wiki page paths used for reasoning.

## Promotion Contract

If an answer is marked high quality, write a distilled version into `wiki/qa/` with:

- original question
- synthesized answer
- source wiki references
- timestamp
