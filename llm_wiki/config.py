from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    raw_dir: Path
    wiki_dir: Path
    outputs_dir: Path
    llm_provider: str
    model: str
    openai_api_key: str
    openai_base_url: str
    temperature_compile: float
    temperature_qa: float
    llm_max_tokens: int
    vision_model: str
    asr_model: str
    tavily_api_key: str
    tavily_base_url: str
    embedding_model: str
    embedding_api_key: str
    embedding_base_url: str
    embedding_dimensions: int
    rerank_model: str
    rerank_api_key: str
    rerank_base_url: str
    retrieval_profile: str
    retrieval_lexical_top_k: int
    retrieval_vector_top_k: int
    retrieval_candidate_max: int
    retrieval_rerank_top_n: int
    retrieval_embedding_batch_size: int
    retrieval_embedding_text_max_chars: int
    max_source_chars: int
    max_context_chars: int


def load_config() -> AppConfig:
    load_dotenv(override=False)

    return AppConfig(
        raw_dir=Path(os.getenv("RAW_DIR", "raw")),
        wiki_dir=Path(os.getenv("WIKI_DIR", "wiki")),
        outputs_dir=Path(os.getenv("OUTPUTS_DIR", "outputs")),
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        model=os.getenv("MODEL", "gpt-5.4-mini"),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://code.rayinai.com/v1").strip(),
        temperature_compile=float(os.getenv("TEMPERATURE_COMPILE", "0.0")),
        temperature_qa=float(os.getenv("TEMPERATURE_QA", "0.0")),
        llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        vision_model=os.getenv("VISION_MODEL", os.getenv("MODEL", "gpt-5.4-mini")).strip(),
        asr_model=os.getenv("ASR_MODEL", "gpt-4o-mini-transcribe").strip(),
        tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip(),
        tavily_base_url=os.getenv("TAVILY_BASE_URL", "https://api.tavily.com").strip(),
        embedding_model=os.getenv("EMBEDDING_MODEL", "").strip(),
        embedding_api_key=os.getenv("EMBEDDING_API_KEY", "").strip(),
        embedding_base_url=os.getenv("EMBEDDING_BASE_URL", "").strip(),
        embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "0")),
        rerank_model=os.getenv("RERANK_MODEL", "").strip(),
        rerank_api_key=os.getenv("RERANK_API_KEY", "").strip(),
        rerank_base_url=os.getenv("RERANK_BASE_URL", "").strip(),
        retrieval_profile=os.getenv("RETRIEVAL_PROFILE", "baseline").strip().lower(),
        retrieval_lexical_top_k=int(os.getenv("RETRIEVAL_LEXICAL_TOP_K", "80")),
        retrieval_vector_top_k=int(os.getenv("RETRIEVAL_VECTOR_TOP_K", "80")),
        retrieval_candidate_max=int(os.getenv("RETRIEVAL_CANDIDATE_MAX", "120")),
        retrieval_rerank_top_n=int(os.getenv("RETRIEVAL_RERANK_TOP_N", "50")),
        retrieval_embedding_batch_size=int(os.getenv("RETRIEVAL_EMBED_BATCH", "16")),
        retrieval_embedding_text_max_chars=int(os.getenv("RETRIEVAL_EMBED_TEXT_MAX_CHARS", "1800")),
        max_source_chars=int(os.getenv("MAX_SOURCE_CHARS", "22000")),
        max_context_chars=int(os.getenv("MAX_CONTEXT_CHARS", "14000")),
    )
