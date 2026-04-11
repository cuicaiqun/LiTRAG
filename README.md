# LLM Wiki RAG

<div align="center">

### Compile-first local knowledge workflow for turning raw files into reusable wiki pages

Works **without a vector database by default**, supports **multi-modal ingest**, and ships with a **dashboard + evaluation loop**.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](#quick-start)
[![OpenAI Compatible](https://img.shields.io/badge/LLM-OpenAI%20Compatible-0A7F5A?style=flat-square)](#configuration)
[![Multi-modal Ingest](https://img.shields.io/badge/Ingest-Multi--modal-B24A35?style=flat-square)](#what-it-does)
[![Dashboard](https://img.shields.io/badge/UI-Dashboard-1F5FA7?style=flat-square)](#dashboard)
[![Eval Ready](https://img.shields.io/badge/Eval-DuReader%20%2B%20QA-D1A245?style=flat-square)](#evaluation)

</div>

> Traditional RAG often reopens the book for every question.  
> This project tries a different route: **ingest first, compile into wiki pages, then retrieve and answer from the wiki**.

## Why This Exists

- **Raw files are not knowledge.** PDFs, images, notes, web captures, and audio/video are first normalized into markdown, then compiled into structured wiki pages.
- **Answer quality should leave artifacts.** Outputs are saved to disk and can be promoted back into the knowledge base.
- **Retrieval should be explainable.** The default path is lexical and file-based; hybrid embedding + rerank is optional, not mandatory.
- **Iteration should be measurable.** Retrieval and QA both have evaluation commands and persisted reports.

## Core Workflow

```text
raw/ -> raw/ingested/*.md -> wiki/sources/*.md -> wiki/index.md + knowledge_map.md + chunk_index.jsonl
                                              -> retrieve -> answer -> outputs/*.md
                                                           -> promote -> wiki/qa/*.md
```

## What It Does

### 1. Multi-modal ingest

- Text, markdown, JSON, HTML
- PDF, DOCX, PPTX
- Images via vision extraction
- Audio/video via FFmpeg + ASR
- Web search capture via Tavily into `raw/web/`

### 2. Compile-first knowledge building

- Compiles each raw source into a structured wiki page
- Builds:
  - `wiki/index.md`
  - `wiki/knowledge_map.md`
  - `wiki/chunk_index.jsonl`
- Supports incremental compile skip using:
  - `file_hash + extractor_version + compile_prompt_version`

### 3. Retrieval profiles

- `baseline`: lexical only
- `hybrid_no_rerank`: lexical + embedding fusion
- `hybrid_rerank`: lexical + embedding fusion + rerank
- If embedding/rerank is unavailable, the pipeline **degrades gracefully** and records the reason

### 4. Ask, save, promote

- Ask questions against compiled wiki knowledge
- Save outputs into `outputs/*.md`
- Optionally promote good answers into `wiki/qa/`

### 5. Dashboard

- Run a local dashboard at `http://127.0.0.1:8787`
- Trigger ingest / compile / search / build-index / ask
- Inspect recent outputs and wiki pages
- Watch task progress, logs, and result previews

## Quick Start

### Install

```bash
# recommended: conda env
conda activate rag
pip install -r requirements.txt
```

Or use `venv` if you prefer.

### Configuration

Copy `.env.example` to `.env` and fill in at least your OpenAI-compatible endpoint and key.

<details>
<summary><strong>Minimal .env</strong></summary>

```bash
LLM_PROVIDER=openai
MODEL=gpt-5.4-mini
OPENAI_BASE_URL=https://code.rayinai.com/v1
OPENAI_API_KEY=your_key
TEMPERATURE_COMPILE=0.0
TEMPERATURE_QA=0.0
LLM_MAX_TOKENS=4096
VISION_MODEL=gpt-5.4-mini
ASR_MODEL=gpt-4o-mini-transcribe
```

</details>

<details>
<summary><strong>Full retrieval / search config</strong></summary>

```bash
TAVILY_BASE_URL=https://api.tavily.com
TAVILY_API_KEY=

EMBEDDING_BASE_URL=
EMBEDDING_API_KEY=
EMBEDDING_MODEL=
EMBEDDING_DIMENSIONS=0

RERANK_BASE_URL=
RERANK_API_KEY=
RERANK_MODEL=

RETRIEVAL_PROFILE=baseline
RETRIEVAL_LEXICAL_TOP_K=80
RETRIEVAL_VECTOR_TOP_K=80
RETRIEVAL_CANDIDATE_MAX=120
RETRIEVAL_RERANK_TOP_N=50
RETRIEVAL_EMBED_BATCH=16
RETRIEVAL_EMBED_TEXT_MAX_CHARS=1800
```

</details>

### Try it in 60 seconds

```bash
python -m llm_wiki init
python -m llm_wiki ingest "D:/data/knowledge/**/*" --compile
python -m llm_wiki ask "RAG 和 LLM Wiki 的关键差异是什么？" --retrieval-profile hybrid_rerank
```

### Launch the dashboard

```bash
python -m llm_wiki dashboard
```

Windows convenience script:

```powershell
.\start_dashboard.ps1
```

## Demo Flow

If you want to show the system in action, the most stable path is:

1. Open the dashboard
2. Show `raw/ingested/*.md`
3. Show `wiki/sources/*.md`
4. Run one `ask`
5. Open the generated `outputs/*.md`
6. Show the evaluation report under `outputs/evals/`

This demonstrates that the project is not just a UI or a script, but a full file-backed workflow.

## Core Commands

### Workspace and compile

```bash
python -m llm_wiki init
python -m llm_wiki compile
python -m llm_wiki build-index
```

### Ingest

```bash
python -m llm_wiki ingest "D:/data/knowledge/**/*"
python -m llm_wiki ingest "D:/data/knowledge/**/*" --compile
```

### Ask

```bash
python -m llm_wiki ask "如何把这个方案用于客服知识库？"
python -m llm_wiki ask "如何把这个方案用于客服知识库？" --promote
python -m llm_wiki ask "你的问题" --retrieval-profile hybrid_rerank
```

### Search

```bash
python -m llm_wiki search "karpathy llm wiki"
python -m llm_wiki search "agent memory design" --compile
```

### Evaluation

```bash
python -m llm_wiki eval-dureader --split dev --ablation
python -m llm_wiki eval-dureader-qa --dataset-path datasets/dev.jsonl/dev.jsonl --max-samples 200 --retrieval-profile hybrid_rerank --seed 42
```

## Why It Is Not Traditional RAG

| Dimension | This project | Traditional RAG |
| --- | --- | --- |
| Primary object | **Compiled wiki pages** | Raw chunks |
| Default retrieval | Lexical / explainable | Usually embedding-first |
| Knowledge lifecycle | Build knowledge first, answer later | Retrieve fragments at question time |
| Output handling | Saved and optionally promoted back | Often ephemeral |
| Best fit | Local knowledge workflow, tens to hundreds of docs | Large-scale retrieval-heavy systems |

The point is not that one approach replaces the other.  
The point is that for a local or small-to-medium knowledge base, **compile-first gives you a cleaner knowledge surface**.

## Supported Formats

<details>
<summary><strong>Current ingest coverage</strong></summary>

- Text: `md markdown txt rst yaml yml csv json html htm`
- Documents: `pdf docx pptx`
- Images: `png jpg jpeg webp bmp gif tif tiff`
- Audio: `mp3 wav m4a aac flac ogg`
- Video transcription: `mp4 mov mkv webm avi`

Notes:

- Legacy `.ppt` is not directly supported; convert to `.pptx` first.
- PDF extraction may fall back to vision OCR when direct text is weak.

</details>

## Retrieval Profiles

| Profile | What it does | Best use |
| --- | --- | --- |
| `baseline` | Lexical only | Default, stable, explainable |
| `hybrid_no_rerank` | Lexical + vector fusion | Better recall without rerank dependency |
| `hybrid_rerank` | Lexical + vector fusion + rerank | Best ranking quality when services are available |

Important:

- Hybrid modes require embedding config.
- `hybrid_rerank` also requires rerank config.
- If those services fail, the system **auto-degrades** and records the reason in outputs/reports.

## Evaluation

### Retrieval: DuReader candidate-set ranking

From the current ablation report:

| Profile | MRR@10 | Recall@1 | Recall@10 |
| --- | --- | --- | --- |
| `baseline` | `0.4121` | `0.2824` | `0.7637` |
| `hybrid_no_rerank` | `0.5048` | `0.3396` | `0.8681` |
| `hybrid_rerank` | `0.7097` | `0.5857` | `0.9505` |

Source:

- `outputs/evals/dureader_retrieval/20260410-002623-dureader-dev.md`

Important boundary:

- This is **candidate-set ranking** on DuReader positives + negatives per query
- It is **not** full-corpus online retrieval over an entire production knowledge base

### QA quality

The project also supports QA evaluation with:

- `Faithfulness`
- `Answer Relevance`
- retry / backoff
- fallback scoring when needed

Important boundary:

- Treat retrieval ablation as the **primary hard evidence**
- Treat QA reports as **supportive quality signals**
- Depending on model/network availability, QA scoring may involve retry/fallback paths, and the report records that explicitly

Source:

- `outputs/evals/dureader_qa/20260410-151506-dureader-dev-qa.md`

## Dashboard

Run it:

```bash
python -m llm_wiki dashboard
```

What you get:

- workspace overview
- recent outputs and wiki pages
- one-click operations for `init`, `ingest`, `search`, `compile`, `build-index`, `ask`
- grouped task progress
- logs and result preview

This is especially useful for demos and iterative local workflows.

## Project Layout

```text
.
├─ raw/
│  ├─ ingested/
│  └─ web/
├─ wiki/
│  ├─ sources/
│  ├─ qa/
│  ├─ index.md
│  ├─ knowledge_map.md
│  ├─ chunk_index.jsonl
│  └─ .compile_manifest.json
├─ outputs/
│  └─ evals/
├─ llm_wiki/
│  ├─ cli.py
│  ├─ ingest.py
│  ├─ compiler.py
│  ├─ retrieve.py
│  ├─ qa.py
│  ├─ dashboard_api.py
│  └─ ...
└─ start_dashboard.ps1
```

## Honest Notes

- This project is best suited for **tens to hundreds of documents**, not massive corpora.
- The dashboard currently uses an in-memory task model, not a production-grade persistent queue.
- Retrieval evaluation is candidate-set based.
- QA evaluation may use retry/fallback depending on runtime conditions.
- If your corpus grows large, you may want to integrate more traditional RAG components later.

## Roadmap

- Deeper integration of `chunk_index.jsonl` into retrieval
- More production-like task persistence for the dashboard
- Stronger graph / entity layer on top of the current knowledge map
- More stable always-online QA scoring pipeline

## Philosophy

This project is not trying to be the biggest RAG stack.  
It is trying to be a **clear, local, explainable, compile-first knowledge workflow** that you can actually inspect, demo, and iterate on.
