# Web Search Capture

- query: llm wiki knowledge base
- captured_at: 20260409-184808
- provider: tavily

## Tavily Answer
An LLM knowledge base uses structured data to reduce hallucinations and stale answers, with vector stores, knowledge graphs, or wikis as core types, emphasizing governance over retrieval architecture.

## Results
### 1. LLM Wiki - GitHub Gist
- url: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- score: 0.9999

index.md is content-oriented. It's a catalog of everything in the wiki — each page listed with a link, a one-line summary, and optionally metadata like date or source count. Organized by category (entities, concepts, sources, etc.). The LLM updates it on every ingest. When answering a query, the LLM reads the index first to find relevant pages, then drills into them. This works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embedding-based RAG infrastructure. [...] Competitive analysis, due diligence, trip planning, course notes, hobby deep-dives — anything where you're accumulating knowledge over time and want it organized rather than scattered. [...] ### Bytekron commented Apr 8, 2026

This is one of the first writeups on “LLM + knowledge base” that actually clicks for me, because it shifts the focus away from pure retrieval and toward accumulation. The line of thinking that stood out most is that most document workflows keep forcing the model to rediscover the same patterns over and over again, while a maintained wiki turns that repeated effort into a durable asset. That feels much closer to how people actually build expertise.

### 2. LLM Knowledge Base: Types, Architecture and Why Most Fail
- url: https://atlan.com/know/what-is-an-llm-knowledge-base/
- score: 0.9998

DigiKey Logo Watch Now

## What the data tells us: the LLM knowledge base is a governance problem

Permalink to “What the data tells us: the LLM knowledge base is a governance problem” #

Both the architecture debate (vector store vs. knowledge graph vs. structured wiki) and the governance layer matter, but they are not equally neglected. Retrieval architecture is a well-understood engineering problem with active tooling, benchmarks, and vendor support. Data governance upstream of the knowledge base is where enterprise teams have less tooling, less attention, and more production failures. That is the imbalance worth correcting. [...] | What it is | An external data store an LLM queries at runtime for domain-specific, current context |
 --- |
| Key benefit | Reduces hallucinations and answer staleness without retraining the model |
| Best for | Enterprise teams with large, changing, or access-controlled knowledge estates |
| Core types | Vector store (RAG), knowledge graph (GraphRAG), structured wiki |
| Primary failure mode | Ungoverned, stale, or undocumented source data; not retrieval architecture |
| Atlan angle | Active metadata catalog as governed knowledge substrate for LLM pipelines |

---

## What is an LLM knowledge base?

Permalink to “What is an LLM knowledge base?” # [...] The Karpathy wiki moment is worth acknowledging directly. In April 2026, Andrej Karpathy shared an approach for personal knowledge bases that skips the vector database entirely: structure your knowledge as a markdown file and let the LLM read it directly in the context window, provided the total is under roughly 100K tokens. VentureBeat covered this in detail. For individuals and small teams with stable, well-curated content, it is a genuinely valid simplification. The enterprise challenge is different: thousands of documents, hundreds of authors, enforced access policies, and continuous data change. That combination requires a more governed architecture. That tension runs through this entire guide.

## How does an LLM knowledge base work?
