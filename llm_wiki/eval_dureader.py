from __future__ import annotations

import gzip
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from .config import AppConfig
from .io_utils import now_filename_stamp, now_stamp, write_text_file
from .retrieval_clients import EmbeddingClient, RerankClient
from .retrieve import (
    EmbeddingCache,
    WikiPage,
    normalize_retrieval_profile,
    retrieve_pages_profile,
    tokenize,
)


DEFAULT_SPLIT_URLS: dict[str, list[str]] = {
    "dev": [
        "https://huggingface.co/datasets/zyznull/dureader-retrieval-dev/resolve/main/dev.jsonl.gz",
    ],
    "train": [
        "https://huggingface.co/datasets/zyznull/dureader-retrieval-train/resolve/main/train.jsonl.gz",
    ],
}


@dataclass(frozen=True)
class DureaderProfileMetrics:
    profile: str
    total_samples: int
    evaluated_samples: int
    skipped_samples: int
    mean_candidates: float
    mrr_at_10: float
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    recall_at_20: float
    recall_at_50: float
    rerank_used_ratio: float
    degraded_ratio: float
    applied_profile_counts: dict[str, int]
    failure_examples: list[dict[str, Any]]


@dataclass(frozen=True)
class DureaderEvalResult:
    split: str
    dataset_path: Path
    retrieval_profile: str
    total_samples: int
    evaluated_samples: int
    skipped_samples: int
    mean_candidates: float
    mrr_at_10: float
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    recall_at_20: float
    recall_at_50: float
    rerank_used_ratio: float
    degraded_ratio: float
    profile_results: dict[str, dict[str, Any]]
    report_json_path: Path
    report_md_path: Path


def _ensure_dataset(
    *,
    split: str,
    data_dir: Path,
    dataset_path: Path | None,
    refresh: bool,
    timeout_sec: int,
) -> Path:
    if dataset_path is not None:
        if not dataset_path.exists() or not dataset_path.is_file():
            raise RuntimeError(f"Dataset file not found: {dataset_path}")
        return dataset_path

    data_dir.mkdir(parents=True, exist_ok=True)
    target = data_dir / f"{split}.jsonl.gz"
    if target.exists() and not refresh:
        return target

    urls = DEFAULT_SPLIT_URLS.get(split) or []
    if not urls:
        raise RuntimeError(f"Unsupported split: {split}")

    last_error = "unknown"
    for url in urls:
        try:
            with requests.get(url, stream=True, timeout=timeout_sec) as resp:
                if resp.status_code >= 400:
                    last_error = f"{url} -> HTTP {resp.status_code}"
                    continue
                with target.open("wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 128):
                        if chunk:
                            f.write(chunk)
                if target.stat().st_size > 0:
                    return target
                last_error = f"{url} -> empty file"
        except Exception as exc:
            last_error = f"{url} -> {exc}"
            continue

    raise RuntimeError(
        f"Failed to download DuReader-Retrieval {split} split. Last error: {last_error}. "
        "You can manually provide --dataset-path <local_jsonl_or_jsonl.gz>."
    )


def _open_text_lines(path: Path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                yield line
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            yield line


def _first_nonempty(record: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _normalize_docid(item: dict[str, Any], fallback: str) -> str:
    for key in ("docid", "doc_id", "id", "pid"):
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return fallback


def _normalize_doc(item: dict[str, Any], *, fallback_docid: str) -> tuple[str, str, str]:
    docid = _normalize_docid(item, fallback_docid)
    title = _first_nonempty(item, ["title", "doc_title", "name"])
    content = _first_nonempty(item, ["text", "content", "passage", "paragraph"])
    return docid, title, content


def _iter_records(dataset_path: Path):
    for line in _open_text_lines(dataset_path):
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _build_query_pages(record: dict[str, Any]) -> tuple[str, list[WikiPage], set[str]]:
    query = _first_nonempty(record, ["query", "question", "qry"])
    positives = record.get("positive_passages") or record.get("positive_ctxs") or []
    negatives = record.get("negative_passages") or record.get("negative_ctxs") or []

    pages: list[WikiPage] = []
    positive_ids: set[str] = set()
    seen_ids: set[str] = set()

    for idx, item in enumerate(positives):
        if not isinstance(item, dict):
            continue
        docid, title, content = _normalize_doc(item, fallback_docid=f"p-{idx}")
        if not content.strip():
            continue
        positive_ids.add(docid)
        if docid in seen_ids:
            continue
        seen_ids.add(docid)
        pages.append(
            WikiPage(
                path=Path(f"doc_{docid}.md"),
                title=title or docid,
                content=content,
                token_freq=Counter(tokenize(f"{title or docid}\n{content}")),
            )
        )

    for idx, item in enumerate(negatives):
        if not isinstance(item, dict):
            continue
        docid, title, content = _normalize_doc(item, fallback_docid=f"n-{idx}")
        if not content.strip() or docid in seen_ids:
            continue
        seen_ids.add(docid)
        pages.append(
            WikiPage(
                path=Path(f"doc_{docid}.md"),
                title=title or docid,
                content=content,
                token_freq=Counter(tokenize(f"{title or docid}\n{content}")),
            )
        )

    return query, pages, positive_ids


def _safe_div(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return num / den


def _new_embedding_client(config: AppConfig) -> EmbeddingClient | None:
    if not (config.embedding_api_key and config.embedding_base_url and config.embedding_model):
        return None
    try:
        return EmbeddingClient(
            api_key=config.embedding_api_key,
            base_url=config.embedding_base_url,
            model=config.embedding_model,
            dimensions=config.embedding_dimensions,
        )
    except Exception:
        return None


def _new_rerank_client(config: AppConfig) -> RerankClient | None:
    if not (config.rerank_api_key and config.rerank_base_url and config.rerank_model):
        return None
    try:
        return RerankClient(
            api_key=config.rerank_api_key,
            base_url=config.rerank_base_url,
            model=config.rerank_model,
        )
    except Exception:
        return None


def _evaluate_profile(
    *,
    records: list[dict[str, Any]],
    profile: str,
    config: AppConfig,
    embedding_client: EmbeddingClient | None,
    rerank_client: RerankClient | None,
    embedding_cache: EmbeddingCache | None,
) -> DureaderProfileMetrics:
    total = 0
    evaluated = 0
    skipped = 0
    sum_candidates = 0
    sum_mrr10 = 0.0
    rerank_used_count = 0
    degraded_count = 0
    applied_profile_counts: Counter[str] = Counter()
    recall_hit = {1: 0, 5: 0, 10: 0, 20: 0, 50: 0}
    failure_examples: list[dict[str, Any]] = []

    for row in records:
        total += 1
        query, pages, positive_ids = _build_query_pages(row)
        if not query or not pages or not positive_ids:
            skipped += 1
            continue

        result = retrieve_pages_profile(
            pages,
            query,
            top_k=50,
            profile=profile,
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

        ranked_ids = [hit.page.path.stem.removeprefix("doc_") for hit in result.hits]
        if not ranked_ids:
            skipped += 1
            continue

        evaluated += 1
        sum_candidates += result.candidate_count
        if result.rerank_used:
            rerank_used_count += 1
        if result.degraded_reason:
            degraded_count += 1
        applied_profile_counts[result.applied_profile] += 1

        first_pos_rank = None
        for idx, docid in enumerate(ranked_ids, start=1):
            if docid in positive_ids:
                first_pos_rank = idx
                break

        if first_pos_rank is not None and first_pos_rank <= 10:
            sum_mrr10 += 1.0 / first_pos_rank
        else:
            if len(failure_examples) < 20:
                failure_examples.append(
                    {
                        "query": query,
                        "positive_docids": sorted(positive_ids)[:8],
                        "top10_docids": ranked_ids[:10],
                        "applied_profile": result.applied_profile,
                    }
                )

        for k in recall_hit:
            topk = ranked_ids[:k]
            if any(docid in positive_ids for docid in topk):
                recall_hit[k] += 1

    return DureaderProfileMetrics(
        profile=profile,
        total_samples=total,
        evaluated_samples=evaluated,
        skipped_samples=skipped,
        mean_candidates=_safe_div(sum_candidates, evaluated),
        mrr_at_10=_safe_div(sum_mrr10, evaluated),
        recall_at_1=_safe_div(recall_hit[1], evaluated),
        recall_at_5=_safe_div(recall_hit[5], evaluated),
        recall_at_10=_safe_div(recall_hit[10], evaluated),
        recall_at_20=_safe_div(recall_hit[20], evaluated),
        recall_at_50=_safe_div(recall_hit[50], evaluated),
        rerank_used_ratio=_safe_div(rerank_used_count, evaluated),
        degraded_ratio=_safe_div(degraded_count, evaluated),
        applied_profile_counts=dict(applied_profile_counts),
        failure_examples=failure_examples,
    )


def run_dureader_retrieval_eval(
    config: AppConfig,
    *,
    split: str = "dev",
    data_dir: Path | None = None,
    dataset_path: Path | None = None,
    max_samples: int | None = 1000,
    refresh: bool = False,
    timeout_sec: int = 120,
    retrieval_profile: str | None = None,
    ablation: bool = False,
) -> DureaderEvalResult:
    split = split.strip().lower()
    if split not in {"dev", "train"}:
        raise RuntimeError("split must be one of: dev, train")

    resolved_data_dir = data_dir or (Path("raw") / "eval_data" / "dureader")
    resolved_dataset = _ensure_dataset(
        split=split,
        data_dir=resolved_data_dir,
        dataset_path=dataset_path,
        refresh=refresh,
        timeout_sec=timeout_sec,
    )
    requested_profile = normalize_retrieval_profile(retrieval_profile or config.retrieval_profile)

    records: list[dict[str, Any]] = []
    for row in _iter_records(resolved_dataset):
        records.append(row)
        if max_samples is not None and max_samples > 0 and len(records) >= max_samples:
            break

    if ablation:
        eval_profiles = ["baseline", "hybrid_no_rerank", "hybrid_rerank"]
    else:
        eval_profiles = [requested_profile]

    embedding_client = _new_embedding_client(config)
    rerank_client = _new_rerank_client(config)
    embedding_cache = EmbeddingCache(path=None) if embedding_client else None

    profile_metrics: list[DureaderProfileMetrics] = []
    for profile in eval_profiles:
        use_embedding = embedding_client if profile != "baseline" else None
        use_rerank = rerank_client if profile == "hybrid_rerank" else None
        metrics = _evaluate_profile(
            records=records,
            profile=profile,
            config=config,
            embedding_client=use_embedding,
            rerank_client=use_rerank,
            embedding_cache=embedding_cache,
        )
        profile_metrics.append(metrics)

    primary = next((item for item in profile_metrics if item.profile == requested_profile), profile_metrics[0])
    profile_results = {
        item.profile: {
            "total_samples": item.total_samples,
            "evaluated_samples": item.evaluated_samples,
            "skipped_samples": item.skipped_samples,
            "mean_candidates": item.mean_candidates,
            "mrr@10": item.mrr_at_10,
            "recall@1": item.recall_at_1,
            "recall@5": item.recall_at_5,
            "recall@10": item.recall_at_10,
            "recall@20": item.recall_at_20,
            "recall@50": item.recall_at_50,
            "rerank_used_ratio": item.rerank_used_ratio,
            "degraded_ratio": item.degraded_ratio,
            "applied_profile_counts": item.applied_profile_counts,
            "failure_examples": item.failure_examples,
        }
        for item in profile_metrics
    }

    out_dir = config.outputs_dir / "evals" / "dureader_retrieval"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = now_filename_stamp()
    json_path = out_dir / f"{ts}-dureader-{split}.json"
    md_path = out_dir / f"{ts}-dureader-{split}.md"

    report = {
        "dataset": "DuReader-Retrieval",
        "split": split,
        "dataset_path": resolved_dataset.as_posix(),
        "evaluated_at": now_stamp(),
        "retrieval_profile": requested_profile,
        "ablation": ablation,
        "profiles": profile_results,
    }
    write_text_file(json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    md_lines = [
        f"# DuReader-Retrieval Eval ({split})",
        "",
        f"- evaluated_at: {report['evaluated_at']}",
        f"- dataset_path: `{resolved_dataset.as_posix()}`",
        f"- retrieval_profile: `{requested_profile}`",
        f"- ablation: `{ablation}`",
        "",
        "## Profile Metrics",
    ]
    for item in profile_metrics:
        md_lines.extend(
            [
                f"### {item.profile}",
                f"- total_samples: {item.total_samples}",
                f"- evaluated_samples: {item.evaluated_samples}",
                f"- skipped_samples: {item.skipped_samples}",
                f"- mean_candidates: {item.mean_candidates:.2f}",
                f"- MRR@10: {item.mrr_at_10:.4f}",
                f"- Recall@1: {item.recall_at_1:.4f}",
                f"- Recall@5: {item.recall_at_5:.4f}",
                f"- Recall@10: {item.recall_at_10:.4f}",
                f"- Recall@20: {item.recall_at_20:.4f}",
                f"- Recall@50: {item.recall_at_50:.4f}",
                f"- rerank_used_ratio: {item.rerank_used_ratio:.4f}",
                f"- degraded_ratio: {item.degraded_ratio:.4f}",
                f"- applied_profile_counts: {json.dumps(item.applied_profile_counts, ensure_ascii=False)}",
                "",
            ]
        )

    md_lines.extend(
        [
            "## Notes",
            "- This evaluation ranks positives + negatives bundled per query (candidate-set ranking),",
            "  not full-corpus retrieval over all DuReader documents.",
            "- Use this for quick iteration and relative comparison of retriever changes.",
        ]
    )
    write_text_file(md_path, "\n".join(md_lines).rstrip() + "\n")

    return DureaderEvalResult(
        split=split,
        dataset_path=resolved_dataset,
        retrieval_profile=requested_profile,
        total_samples=primary.total_samples,
        evaluated_samples=primary.evaluated_samples,
        skipped_samples=primary.skipped_samples,
        mean_candidates=primary.mean_candidates,
        mrr_at_10=primary.mrr_at_10,
        recall_at_1=primary.recall_at_1,
        recall_at_5=primary.recall_at_5,
        recall_at_10=primary.recall_at_10,
        recall_at_20=primary.recall_at_20,
        recall_at_50=primary.recall_at_50,
        rerank_used_ratio=primary.rerank_used_ratio,
        degraded_ratio=primary.degraded_ratio,
        profile_results=profile_results,
        report_json_path=json_path,
        report_md_path=md_path,
    )
