from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .io_utils import read_text_file
from .retrieval_clients import EmbeddingClient, RerankClient

LATIN_RE = re.compile(r"[a-z0-9_]+")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "have",
    "what",
    "how",
    "why",
    "when",
    "where",
    "which",
    "you",
    "your",
    "are",
    "is",
    "of",
    "to",
    "in",
    "on",
    "a",
    "an",
}

SUPPORTED_RETRIEVAL_PROFILES = {"baseline", "hybrid_no_rerank", "hybrid_rerank"}

QUERY_ALIAS_RULES: list[tuple[str, str]] = [
    (r"\bwmp\b", "windows media player"),
    (r"\bqq\b", "腾讯qq"),
    (r"\bcad\b", "autocad"),
    (r"\bps\b", "photoshop"),
    (r"\bppt\b", "powerpoint"),
]

RRF_K = 60.0


@dataclass(frozen=True)
class WikiPage:
    path: Path
    title: str
    content: str
    token_freq: Counter[str]


@dataclass(frozen=True)
class RetrievalHit:
    page: WikiPage
    final_score: float
    lexical_score: float = 0.0
    vector_score: float = 0.0
    rerank_score: float = 0.0
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalResult:
    requested_profile: str
    applied_profile: str
    normalized_query: str
    candidate_count: int
    rerank_used: bool
    degraded_reason: str
    hits: list[RetrievalHit]


@dataclass
class _CandidateState:
    page: WikiPage
    lexical_score: float = 0.0
    vector_score: float = 0.0
    fused_score: float = 0.0
    rerank_score: float = 0.0
    sources: set[str] = field(default_factory=set)


class EmbeddingCache:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._data: dict[str, list[float]] = {}
        self._dirty = 0
        if self.path and self.path.exists():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    for key, value in payload.items():
                        if isinstance(key, str) and isinstance(value, list) and value:
                            self._data[key] = [float(x) for x in value]
            except Exception:
                self._data = {}

    def get(self, key: str) -> list[float] | None:
        return self._data.get(key)

    def set(self, key: str, vector: list[float]) -> None:
        if not vector:
            return
        self._data[key] = [float(x) for x in vector]
        self._dirty += 1
        if self.path and self._dirty >= 64:
            self.flush()

    def flush(self) -> None:
        if not self.path or self._dirty <= 0:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False), encoding="utf-8")
        self._dirty = 0


def normalize_retrieval_profile(profile: str | None) -> str:
    value = (profile or "baseline").strip().lower()
    if value not in SUPPORTED_RETRIEVAL_PROFILES:
        return "baseline"
    return value


def normalize_query(query: str) -> str:
    normalized = unicodedata.normalize("NFKC", query or "").lower().strip()
    for pattern, replacement in QUERY_ALIAS_RULES:
        normalized = re.sub(pattern, f" {replacement} ", normalized)
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    latin_tokens = LATIN_RE.findall(lowered)
    cjk_tokens = CJK_RE.findall(text)
    return [t for t in latin_tokens + cjk_tokens if t and t not in STOPWORDS]


def extract_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            if title:
                return title
    return fallback


def load_wiki_pages(wiki_dir: Path) -> list[WikiPage]:
    if not wiki_dir.exists():
        return []

    pages: list[WikiPage] = []
    for path in sorted(wiki_dir.rglob("*.md")):
        if path.name in {"index.md", "knowledge_map.md"}:
            continue
        text = read_text_file(path)
        if not text.strip():
            continue
        title = extract_title(text, path.stem)
        freq = Counter(tokenize(f"{title}\n{text}"))
        pages.append(WikiPage(path=path, title=title, content=text, token_freq=freq))
    return pages


def _lexical_score(page: WikiPage, query_tokens: list[str]) -> float:
    if not query_tokens:
        return 0.0
    title_lower = page.title.lower()
    score = 0.0
    for token in query_tokens:
        tf = page.token_freq.get(token, 0)
        if tf:
            score += 1.0 + min(4, tf) * 0.35
            if token in title_lower:
                score += 1.2
    return score


def _rank_lexical(pages: list[WikiPage], query: str, top_k: int) -> list[tuple[WikiPage, float]]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    ranked: list[tuple[WikiPage, float]] = []
    for page in pages:
        score = _lexical_score(page, query_tokens)
        if score > 0:
            ranked.append((page, score))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:top_k]


def _hash_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _embedding_text(page: WikiPage, max_chars: int) -> str:
    return f"{page.title}\n{page.content[:max_chars]}".strip()


def _query_embedding(
    normalized_query: str,
    *,
    embedding_client: EmbeddingClient,
    embedding_cache: EmbeddingCache | None,
) -> list[float]:
    cache_key = f"q:{embedding_client.model}:{_hash_text(normalized_query)}"
    if embedding_cache:
        cached = embedding_cache.get(cache_key)
        if cached is not None:
            return cached
    vectors = embedding_client.embed_texts([normalized_query])
    if not vectors:
        raise RuntimeError("Embedding query vector is empty.")
    query_vec = vectors[0]
    if embedding_cache:
        embedding_cache.set(cache_key, query_vec)
    return query_vec


def _page_embeddings(
    pages: list[WikiPage],
    *,
    embedding_client: EmbeddingClient,
    embedding_cache: EmbeddingCache | None,
    embedding_batch_size: int,
    embedding_text_max_chars: int,
) -> dict[str, list[float]]:
    by_key: dict[str, list[float]] = {}
    missing_texts: list[str] = []
    missing_keys: list[str] = []
    missing_page_keys: list[str] = []

    for page in pages:
        page_key = page.path.as_posix()
        text = _embedding_text(page, embedding_text_max_chars)
        text_key = f"d:{embedding_client.model}:{_hash_text(text)}"
        if embedding_cache:
            cached = embedding_cache.get(text_key)
            if cached is not None:
                by_key[page_key] = cached
                continue
        missing_texts.append(text)
        missing_keys.append(text_key)
        missing_page_keys.append(page_key)

    batch_size = max(1, embedding_batch_size)
    for start in range(0, len(missing_texts), batch_size):
        text_batch = missing_texts[start : start + batch_size]
        vectors = embedding_client.embed_texts(text_batch)
        if len(vectors) != len(text_batch):
            raise RuntimeError("Embedding batch result size mismatch.")
        for offset, vector in enumerate(vectors):
            idx = start + offset
            page_key = missing_page_keys[idx]
            text_key = missing_keys[idx]
            by_key[page_key] = vector
            if embedding_cache:
                embedding_cache.set(text_key, vector)
    return by_key


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n <= 0:
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for i in range(n):
        av = a[i]
        bv = b[i]
        dot += av * bv
        norm_a += av * av
        norm_b += bv * bv
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def _rank_vector(
    pages: list[WikiPage],
    normalized_query: str,
    *,
    embedding_client: EmbeddingClient,
    embedding_cache: EmbeddingCache | None,
    top_k: int,
    embedding_batch_size: int,
    embedding_text_max_chars: int,
) -> list[tuple[WikiPage, float]]:
    if not pages:
        return []
    query_vec = _query_embedding(
        normalized_query,
        embedding_client=embedding_client,
        embedding_cache=embedding_cache,
    )
    page_vectors = _page_embeddings(
        pages,
        embedding_client=embedding_client,
        embedding_cache=embedding_cache,
        embedding_batch_size=embedding_batch_size,
        embedding_text_max_chars=embedding_text_max_chars,
    )
    ranked: list[tuple[WikiPage, float]] = []
    for page in pages:
        vector = page_vectors.get(page.path.as_posix())
        if not vector:
            continue
        sim = _cosine_similarity(query_vec, vector)
        ranked.append((page, sim))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:top_k]


def _to_hits(
    ranked: list[_CandidateState],
    *,
    top_k: int,
    use_rerank_score: bool,
) -> list[RetrievalHit]:
    output: list[RetrievalHit] = []
    for idx, item in enumerate(ranked):
        if idx >= top_k:
            break
        final_score = item.rerank_score if use_rerank_score else item.fused_score
        output.append(
            RetrievalHit(
                page=item.page,
                final_score=final_score,
                lexical_score=item.lexical_score,
                vector_score=item.vector_score,
                rerank_score=item.rerank_score,
                sources=tuple(sorted(item.sources)),
            )
        )
    return output


def retrieve_pages_profile(
    pages: list[WikiPage],
    query: str,
    *,
    top_k: int = 6,
    profile: str = "baseline",
    embedding_client: EmbeddingClient | None = None,
    rerank_client: RerankClient | None = None,
    embedding_cache: EmbeddingCache | None = None,
    lexical_top_k: int = 80,
    vector_top_k: int = 80,
    candidate_max: int = 120,
    rerank_top_n: int = 50,
    embedding_batch_size: int = 16,
    embedding_text_max_chars: int = 1800,
) -> RetrievalResult:
    requested_profile = normalize_retrieval_profile(profile)
    normalized_query = normalize_query(query)
    if not normalized_query:
        return RetrievalResult(
            requested_profile=requested_profile,
            applied_profile="baseline",
            normalized_query="",
            candidate_count=0,
            rerank_used=False,
            degraded_reason="empty_query",
            hits=[],
        )

    lexical_hits = _rank_lexical(
        pages,
        normalized_query,
        top_k=max(top_k, max(1, lexical_top_k)),
    )

    if requested_profile == "baseline":
        hits = [
            RetrievalHit(
                page=page,
                final_score=score,
                lexical_score=score,
                sources=("lexical",),
            )
            for page, score in lexical_hits[:top_k]
        ]
        return RetrievalResult(
            requested_profile=requested_profile,
            applied_profile="baseline",
            normalized_query=normalized_query,
            candidate_count=len(lexical_hits),
            rerank_used=False,
            degraded_reason="",
            hits=hits,
        )

    degraded: list[str] = []
    candidates: dict[str, _CandidateState] = {}

    lexical_limit = max(1, lexical_top_k)
    for rank, (page, score) in enumerate(lexical_hits[:lexical_limit], start=1):
        key = page.path.as_posix()
        current = candidates.get(key)
        if current is None:
            current = _CandidateState(page=page)
            candidates[key] = current
        current.lexical_score = max(current.lexical_score, score)
        current.fused_score += 1.0 / (RRF_K + rank)
        current.sources.add("lexical")

    vector_hits: list[tuple[WikiPage, float]] = []
    vector_used = False
    if embedding_client is None:
        degraded.append("embedding_unavailable")
    else:
        try:
            vector_hits = _rank_vector(
                pages,
                normalized_query,
                embedding_client=embedding_client,
                embedding_cache=embedding_cache,
                top_k=max(top_k, max(1, vector_top_k)),
                embedding_batch_size=embedding_batch_size,
                embedding_text_max_chars=embedding_text_max_chars,
            )
            vector_used = len(vector_hits) > 0
        except Exception as exc:
            degraded.append(f"embedding_error={exc}")
            vector_hits = []
            vector_used = False

    vector_limit = max(1, vector_top_k)
    for rank, (page, sim) in enumerate(vector_hits[:vector_limit], start=1):
        key = page.path.as_posix()
        current = candidates.get(key)
        if current is None:
            current = _CandidateState(page=page)
            candidates[key] = current
        current.vector_score = max(current.vector_score, sim)
        current.fused_score += 1.0 / (RRF_K + rank)
        current.sources.add("vector")

    if not candidates:
        return RetrievalResult(
            requested_profile=requested_profile,
            applied_profile="baseline",
            normalized_query=normalized_query,
            candidate_count=0,
            rerank_used=False,
            degraded_reason="; ".join(degraded) if degraded else "no_candidates",
            hits=[],
        )

    merged = sorted(
        candidates.values(),
        key=lambda item: (item.fused_score, item.lexical_score, item.vector_score),
        reverse=True,
    )
    merged = merged[: max(1, candidate_max)]

    rerank_used = False
    applied_profile = "hybrid_no_rerank" if vector_used else "baseline"
    if requested_profile == "hybrid_rerank" and vector_used:
        if rerank_client is None:
            degraded.append("rerank_unavailable")
        else:
            rerank_pool = merged[: max(1, min(len(merged), rerank_top_n))]
            docs = [f"{item.page.title}\n{item.page.content[:2000]}".strip() for item in rerank_pool]
            try:
                rerank_scores = rerank_client.rerank(
                    query=normalized_query,
                    documents=docs,
                    top_n=len(docs),
                )
                if len(rerank_scores) != len(rerank_pool):
                    raise RuntimeError("rerank size mismatch")
                for item, score in zip(rerank_pool, rerank_scores):
                    item.rerank_score = float(score)
                    item.sources.add("rerank")
                rerank_pool.sort(key=lambda item: (item.rerank_score, item.fused_score), reverse=True)
                tail = merged[len(rerank_pool) :]
                merged = rerank_pool + tail
                rerank_used = True
                applied_profile = "hybrid_rerank"
            except Exception as exc:
                degraded.append(f"rerank_error={exc}")
                applied_profile = "hybrid_no_rerank" if vector_used else "baseline"

    hits = _to_hits(merged, top_k=max(1, top_k), use_rerank_score=rerank_used)
    if embedding_cache:
        embedding_cache.flush()

    return RetrievalResult(
        requested_profile=requested_profile,
        applied_profile=applied_profile,
        normalized_query=normalized_query,
        candidate_count=len(merged),
        rerank_used=rerank_used,
        degraded_reason="; ".join(degraded),
        hits=hits,
    )


def retrieve_pages(pages: list[WikiPage], query: str, top_k: int = 6) -> list[tuple[WikiPage, float]]:
    result = retrieve_pages_profile(
        pages,
        query,
        top_k=top_k,
        profile="baseline",
    )
    return [(hit.page, hit.final_score) for hit in result.hits]
