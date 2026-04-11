from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig
from .io_utils import ensure_workspace, now_filename_stamp, now_stamp, safe_slug, write_text_file
from .llm import LLMClient
from .retrieval_clients import EmbeddingClient, RerankClient
from .retrieve import EmbeddingCache, WikiPage, load_wiki_pages, normalize_retrieval_profile, retrieve_pages_profile


QA_SYSTEM_PROMPT = """You are answering from a compiled wiki knowledge base.
Rules:
- Use only the provided wiki context.
- If context is insufficient, explicitly say what is missing.
- Be concise and practical.
- Cite supporting pages in parentheses, like: (wiki/sources/page-name.md)."""


@dataclass(frozen=True)
class AskResult:
    output_path: Path
    used_pages: list[Path]
    answer: str
    retrieval_requested_profile: str
    retrieval_applied_profile: str
    retrieval_degraded_reason: str


def _render_context(ranked: list[tuple[WikiPage, float]], max_chars: int) -> str:
    blocks: list[str] = []
    used = 0
    for page, score in ranked:
        snippet = page.content[:2200]
        block = f"[{page.path.as_posix()} | score={score:.2f}]\n{snippet}\n"
        if used + len(block) > max_chars:
            break
        blocks.append(block)
        used += len(block)
    return "\n".join(blocks)


def ask_wiki(
    config: AppConfig,
    *,
    question: str,
    llm: LLMClient,
    top_k: int = 6,
    promote: bool = False,
    retrieval_profile: str | None = None,
) -> AskResult:
    ensure_workspace(config.raw_dir, config.wiki_dir, config.outputs_dir)
    pages = load_wiki_pages(config.wiki_dir)
    requested_profile = normalize_retrieval_profile(retrieval_profile or config.retrieval_profile)

    embedding_client: EmbeddingClient | None = None
    rerank_client: RerankClient | None = None
    embedding_cache: EmbeddingCache | None = None

    if requested_profile != "baseline":
        if config.embedding_api_key and config.embedding_base_url and config.embedding_model:
            try:
                embedding_client = EmbeddingClient(
                    api_key=config.embedding_api_key,
                    base_url=config.embedding_base_url,
                    model=config.embedding_model,
                    dimensions=config.embedding_dimensions,
                )
                cache_slug = safe_slug(config.embedding_model, max_len=40)
                cache_path = config.outputs_dir / "cache" / f"embeddings-{cache_slug}.json"
                embedding_cache = EmbeddingCache(path=cache_path)
            except Exception:
                embedding_client = None
                embedding_cache = None
        if requested_profile == "hybrid_rerank":
            if config.rerank_api_key and config.rerank_base_url and config.rerank_model:
                try:
                    rerank_client = RerankClient(
                        api_key=config.rerank_api_key,
                        base_url=config.rerank_base_url,
                        model=config.rerank_model,
                    )
                except Exception:
                    rerank_client = None

    retrieval_result = retrieve_pages_profile(
        pages,
        question,
        top_k=top_k,
        profile=requested_profile,
        embedding_client=embedding_client,
        rerank_client=rerank_client,
        embedding_cache=embedding_cache,
        lexical_top_k=config.retrieval_lexical_top_k,
        vector_top_k=config.retrieval_vector_top_k,
        candidate_max=config.retrieval_candidate_max,
        rerank_top_n=config.retrieval_rerank_top_n,
        embedding_batch_size=config.retrieval_embedding_batch_size,
        embedding_text_max_chars=config.retrieval_embedding_text_max_chars,
    )
    ranked = [(hit.page, hit.final_score) for hit in retrieval_result.hits]

    context = _render_context(ranked, config.max_context_chars)
    user_prompt = (
        f"Question:\n{question}\n\n"
        "Wiki context:\n"
        f"{context}\n\n"
        "Provide a direct answer with explicit citations."
    )
    answer = llm.complete(
        model=config.model,
        system_prompt=QA_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=config.temperature_qa,
        max_tokens=config.llm_max_tokens,
    )

    used_pages = [page.path for page, _ in ranked]
    ts = now_filename_stamp()
    q_slug = safe_slug(question, max_len=48)
    output_path = config.outputs_dir / f"{ts}-{q_slug}.md"

    output_text = [
        f"# Q&A Output ({ts})",
        "",
        f"## Question",
        question,
        "",
        "## Retrieval",
        f"- requested_profile: {retrieval_result.requested_profile}",
        f"- applied_profile: {retrieval_result.applied_profile}",
        f"- candidate_count: {retrieval_result.candidate_count}",
        f"- rerank_used: {retrieval_result.rerank_used}",
    ]
    if retrieval_result.degraded_reason:
        output_text.append(f"- degraded_reason: {retrieval_result.degraded_reason}")
    output_text += [
        "",
        "## Used Wiki Pages",
    ]
    if used_pages:
        output_text.extend(f"- {path.as_posix()}" for path in used_pages)
    else:
        output_text.append("- (none)")
    output_text += [
        "",
        "## Answer",
        answer.strip(),
        "",
        f"_Generated at {now_stamp()}_",
    ]

    write_text_file(output_path, "\n".join(output_text).rstrip() + "\n")

    if promote:
        promote_path = config.wiki_dir / "qa" / f"{ts}-{q_slug}.md"
        promote_text = [
            f"# QA Note: {question}",
            "",
            f"- Created: {now_stamp()}",
            f"- requested_profile: {retrieval_result.requested_profile}",
            f"- applied_profile: {retrieval_result.applied_profile}",
            "",
            "## Answer",
            answer.strip(),
            "",
            "## Evidence Pages",
        ]
        if used_pages:
            promote_text.extend(f"- `{path.as_posix()}`" for path in used_pages)
        else:
            promote_text.append("- (none)")
        write_text_file(promote_path, "\n".join(promote_text).rstrip() + "\n")

    return AskResult(
        output_path=output_path,
        used_pages=used_pages,
        answer=answer,
        retrieval_requested_profile=retrieval_result.requested_profile,
        retrieval_applied_profile=retrieval_result.applied_profile,
        retrieval_degraded_reason=retrieval_result.degraded_reason,
    )
