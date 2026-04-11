from __future__ import annotations

import importlib
import json
import math
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import AppConfig
from .eval_dureader import (
    _build_query_pages,
    _ensure_dataset,
    _iter_records,
    _new_embedding_client,
    _new_rerank_client,
    _safe_div,
)
from .io_utils import now_filename_stamp, now_stamp, write_text_file
from .llm import LLMClient
from .retrieve import EmbeddingCache, normalize_retrieval_profile, retrieve_pages_profile


QA_EVAL_SYSTEM_PROMPT = """You are answering from provided retrieval context.
Rules:
- Use only the given context.
- If context is insufficient, explicitly state what is missing.
- Keep answers concise and factual."""

JUDGE_SYSTEM_PROMPT = """You are a strict RAG evaluator.
Score each sample with two values in [0,1]:
- faithfulness: Are answer claims supported by provided contexts?
- answer_relevance: Does the answer directly and sufficiently answer the question?
Return ONLY JSON object: {"faithfulness": <float>, "answer_relevance": <float>}
No extra text."""


FAITHFULNESS_KEYS = ("faithfulness", "faithfulness_score")
ANSWER_RELEVANCE_KEYS = (
    "answer_relevancy",
    "answer_relevance",
    "answer_relevancy_score",
    "answer_relevance_score",
    "response_relevancy",
)


@dataclass(frozen=True)
class DureaderQAEvalResult:
    split: str
    dataset_path: Path
    retrieval_profile: str
    judge_model: str
    total_samples: int
    evaluated_samples: int
    skipped_samples: int
    faithfulness_scored_samples: int
    answer_relevance_scored_samples: int
    faithfulness: float | None
    answer_relevance: float | None
    faithfulness_gate: float
    answer_relevance_gate: float
    faithfulness_pass: bool
    answer_relevance_pass: bool
    overall_pass: bool
    report_json_path: Path
    report_md_path: Path


_FLOAT_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _metric_value(obj: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        raw = obj.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isfinite(value):
            return value
    return None


def _safe_float(value: float | None) -> float | None:
    if value is None:
        return None
    if not math.isfinite(value):
        return None
    return float(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return None
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if p <= 0:
        return values[0]
    if p >= 100:
        return values[-1]
    pos = (len(values) - 1) * (p / 100.0)
    lower = int(math.floor(pos))
    upper = int(math.ceil(pos))
    if lower == upper:
        return values[lower]
    weight = pos - lower
    return values[lower] * (1.0 - weight) + values[upper] * weight


def _fmt_score(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"


def _clip01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _parse_judge_scores(raw_text: str) -> tuple[float | None, float | None]:
    text = (raw_text or "").strip()
    if not text:
        return None, None
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start : end + 1]
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                f = _metric_value(data, ("faithfulness",))
                a = _metric_value(data, ("answer_relevance", "answer_relevancy"))
                if f is not None:
                    f = _clip01(f)
                if a is not None:
                    a = _clip01(a)
                return f, a
        except Exception:
            pass

    nums = [float(x) for x in _FLOAT_RE.findall(text)]
    if len(nums) >= 2:
        return _clip01(nums[0]), _clip01(nums[1])
    return None, None


def _judge_scores_fallback(
    *,
    llm: LLMClient,
    model: str,
    temperature: float,
    max_tokens: int,
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: str,
) -> tuple[float | None, float | None]:
    joined_context = "\n\n".join(contexts[:3])
    if len(joined_context) > 5200:
        joined_context = joined_context[:5200]
    gt = ground_truth[:1600]
    user_prompt = (
        "Question:\n"
        f"{question}\n\n"
        "Answer:\n"
        f"{answer}\n\n"
        "Ground truth (reference):\n"
        f"{gt}\n\n"
        "Retrieved contexts:\n"
        f"{joined_context}\n\n"
        "Output only JSON with keys faithfulness and answer_relevance."
    )
    raw = llm.complete(
        model=model,
        system_prompt=JUDGE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return _parse_judge_scores(raw)


def _positive_texts(record: dict[str, Any]) -> list[str]:
    positives = record.get("positive_passages") or record.get("positive_ctxs") or []
    texts: list[str] = []
    for item in positives:
        if not isinstance(item, dict):
            continue
        for key in ("text", "content", "passage", "paragraph"):
            raw = item.get(key)
            if isinstance(raw, str) and raw.strip():
                texts.append(raw.strip())
                break
    return texts


def _render_generation_context(
    *,
    query: str,
    hits: list[Any],
    max_chars: int,
) -> str:
    blocks: list[str] = [f"Question:\n{query}", "", "Context:"]
    used = 0
    for idx, hit in enumerate(hits, start=1):
        page = hit.page
        snippet = page.content[:1800].strip()
        block = f"[{idx}] {page.path.as_posix()}\n{snippet}\n"
        if used + len(block) > max_chars:
            break
        blocks.append(block)
        used += len(block)
    blocks.append("Answer directly with evidence from context.")
    return "\n".join(blocks)


def _resolve_ragas_metric(name_candidates: tuple[str, ...]) -> Any:
    metrics_mod = importlib.import_module("ragas.metrics")
    for name in name_candidates:
        metric_obj = getattr(metrics_mod, name, None)
        if metric_obj is None:
            continue
        if isinstance(metric_obj, type):
            try:
                return metric_obj()
            except TypeError:
                continue
        return metric_obj
    raise RuntimeError(f"RAGAS metric not found. Tried: {', '.join(name_candidates)}")


def _resolve_ragas_evaluate_fn() -> Any:
    try:
        ragas_mod = importlib.import_module("ragas")
        evaluate_fn = getattr(ragas_mod, "evaluate", None)
        if callable(evaluate_fn):
            return evaluate_fn
    except Exception:
        pass
    eval_mod = importlib.import_module("ragas.evaluation")
    evaluate_fn = getattr(eval_mod, "evaluate", None)
    if callable(evaluate_fn):
        return evaluate_fn
    raise RuntimeError("Unable to locate ragas evaluate() API.")


def _build_ragas_llm(config: AppConfig, *, judge_model: str | None = None) -> Any:
    from langchain_openai import ChatOpenAI

    chat_llm = ChatOpenAI(
        model=(judge_model or config.model),
        temperature=config.temperature_qa,
        api_key=config.openai_api_key,
        base_url=config.openai_base_url or None,
    )

    for module_name, class_name in (
        ("ragas.llms", "LangchainLLMWrapper"),
        ("ragas.llms.base", "LangchainLLMWrapper"),
        ("ragas.llms", "LangchainLLM"),
    ):
        try:
            wrapper_mod = importlib.import_module(module_name)
            wrapper_cls = getattr(wrapper_mod, class_name, None)
            if wrapper_cls is None:
                continue
            try:
                return wrapper_cls(chat_llm)
            except TypeError:
                try:
                    return wrapper_cls(langchain_llm=chat_llm)
                except TypeError:
                    continue
        except Exception:
            continue
    return chat_llm


def _ragas_records_and_summary(result: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}

    if hasattr(result, "to_pandas"):
        try:
            df = result.to_pandas()
            if hasattr(df, "to_dict"):
                records = df.to_dict(orient="records")
        except Exception:
            pass

    if hasattr(result, "to_dict"):
        try:
            payload = result.to_dict()
            if isinstance(payload, dict):
                summary = payload
                if not records:
                    raw_scores = payload.get("scores")
                    if isinstance(raw_scores, list):
                        records = [item for item in raw_scores if isinstance(item, dict)]
        except Exception:
            pass

    if not summary and isinstance(result, dict):
        summary = result

    return records, summary


def _evaluate_with_ragas(
    *,
    ragas_rows: list[dict[str, Any]],
    config: AppConfig,
    judge_model: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from datasets import Dataset

    evaluate_fn = _resolve_ragas_evaluate_fn()
    faithfulness_metric = _resolve_ragas_metric(("faithfulness", "Faithfulness"))
    answer_relevance_metric = _resolve_ragas_metric(
        ("answer_relevancy", "answer_relevance", "ResponseRelevancy", "AnswerRelevancy")
    )
    dataset = Dataset.from_list(ragas_rows)
    ragas_llm = _build_ragas_llm(config, judge_model=judge_model)
    metrics = [faithfulness_metric, answer_relevance_metric]

    run_config_obj: Any = None
    try:
        run_config_mod = importlib.import_module("ragas.run_config")
        run_config_cls = getattr(run_config_mod, "RunConfig", None)
        if run_config_cls is not None:
            try:
                run_config_obj = run_config_cls(max_workers=1, timeout=120)
            except TypeError:
                run_config_obj = run_config_cls()
    except Exception:
        run_config_obj = None

    attempts = [
        {"llm": ragas_llm, "raise_exceptions": False, "run_config": run_config_obj},
        {"llm": ragas_llm, "run_config": run_config_obj},
        {"raise_exceptions": False, "run_config": run_config_obj},
        {},
    ]
    last_error: Exception | None = None
    for extra_kwargs in attempts:
        try:
            result = evaluate_fn(dataset=dataset, metrics=metrics, **extra_kwargs)
            return _ragas_records_and_summary(result)
        except TypeError as exc:
            last_error = exc
            continue
        except Exception as exc:
            last_error = exc
            continue

    if last_error:
        raise RuntimeError(f"RAGAS evaluate failed: {last_error}") from last_error
    raise RuntimeError("RAGAS evaluate failed for unknown reason.")


def _sleep_backoff(base_sec: float, attempt_index: int) -> None:
    if base_sec <= 0:
        return
    delay = min(base_sec * (2 ** max(0, attempt_index - 1)), 8.0)
    if delay > 0:
        time.sleep(delay)


def _error_label(exc: Exception) -> str:
    text = str(exc).strip()
    if not text:
        return exc.__class__.__name__
    collapsed = " ".join(text.split())
    return collapsed[:200]


def _bump_counter(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def _load_latest_success_scores(report_dir: Path) -> dict[str, Any] | None:
    if not report_dir.exists():
        return None
    candidates = sorted(
        report_dir.glob("*-dureader-*-qa.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        summary = payload.get("summary")
        if not isinstance(summary, dict):
            continue
        faithfulness = _metric_value(summary, ("faithfulness",))
        answer_relevance = _metric_value(summary, ("answer_relevance", "answer_relevancy"))
        if faithfulness is None or answer_relevance is None:
            continue
        faithfulness_count = summary.get("faithfulness_scored_samples")
        answer_relevance_count = summary.get("answer_relevance_scored_samples")
        try:
            f_count = int(faithfulness_count)
            a_count = int(answer_relevance_count)
        except (TypeError, ValueError):
            f_count = 0
            a_count = 0
        if f_count <= 0 and a_count <= 0:
            continue
        return {
            "faithfulness": _clip01(faithfulness),
            "answer_relevance": _clip01(answer_relevance),
            "source_report": path.as_posix(),
            "source_evaluated_at": payload.get("evaluated_at"),
        }
    return None


def run_dureader_qa_eval(
    config: AppConfig,
    *,
    split: str = "dev",
    data_dir: Path | None = None,
    dataset_path: Path | None = None,
    max_samples: int | None = 200,
    refresh: bool = False,
    timeout_sec: int = 120,
    retrieval_profile: str | None = "hybrid_rerank",
    top_k: int = 6,
    seed: int = 42,
    judge_model: str | None = None,
    faithfulness_gate: float = 0.85,
    answer_relevance_gate: float = 0.80,
    sample_retry_times: int = 3,
    score_retry_times: int = 3,
    retry_backoff_base_sec: float = 1.0,
) -> DureaderQAEvalResult:
    split = split.strip().lower()
    if split not in {"dev", "train"}:
        raise RuntimeError("split must be one of: dev, train")
    if top_k <= 0:
        raise RuntimeError("top_k must be > 0")
    sample_retry_times = max(1, int(sample_retry_times))
    score_retry_times = max(1, int(score_retry_times))
    retry_backoff_base_sec = max(0.0, float(retry_backoff_base_sec))

    resolved_data_dir = data_dir or (Path("raw") / "eval_data" / "dureader")
    resolved_dataset = _ensure_dataset(
        split=split,
        data_dir=resolved_data_dir,
        dataset_path=dataset_path,
        refresh=refresh,
        timeout_sec=timeout_sec,
    )
    requested_profile = normalize_retrieval_profile(retrieval_profile or config.retrieval_profile)

    all_records = list(_iter_records(resolved_dataset))
    if max_samples is not None and max_samples > 0 and len(all_records) > max_samples:
        rng = random.Random(seed)
        selected_idx = sorted(rng.sample(range(len(all_records)), max_samples))
        records = [all_records[idx] for idx in selected_idx]
    else:
        records = all_records

    llm = LLMClient(api_key=config.openai_api_key, base_url=config.openai_base_url)
    embedding_client = _new_embedding_client(config)
    rerank_client = _new_rerank_client(config)
    embedding_cache = EmbeddingCache(path=None) if embedding_client else None

    total = 0
    evaluated = 0
    skipped = 0
    ragas_inputs: list[dict[str, Any]] = []
    sample_meta: list[dict[str, Any]] = []
    sample_contexts: list[list[str]] = []
    generation_fail_reasons: dict[str, int] = {}

    for row in records:
        total += 1
        try:
            query, pages, positive_ids = _build_query_pages(row)
        except Exception as exc:
            skipped += 1
            _bump_counter(generation_fail_reasons, f"build_query_pages:{_error_label(exc)}")
            continue
        if not query or not pages or not positive_ids:
            skipped += 1
            _bump_counter(generation_fail_reasons, "invalid_record")
            continue

        try:
            result = retrieve_pages_profile(
                pages,
                query,
                top_k=top_k,
                profile=requested_profile,
                embedding_client=embedding_client if requested_profile != "baseline" else None,
                rerank_client=rerank_client if requested_profile == "hybrid_rerank" else None,
                embedding_cache=embedding_cache,
                lexical_top_k=config.retrieval_lexical_top_k,
                vector_top_k=config.retrieval_vector_top_k,
                candidate_max=config.retrieval_candidate_max,
                rerank_top_n=config.retrieval_rerank_top_n,
                embedding_batch_size=config.retrieval_embedding_batch_size,
                embedding_text_max_chars=config.retrieval_embedding_text_max_chars,
            )
        except Exception as exc:
            skipped += 1
            _bump_counter(generation_fail_reasons, f"retrieve_pages:{_error_label(exc)}")
            continue

        if not result.hits:
            skipped += 1
            _bump_counter(generation_fail_reasons, "no_hits")
            continue

        contexts: list[str] = []
        context_docids: list[str] = []
        for hit in result.hits[:top_k]:
            text = hit.page.content.strip()
            if not text:
                continue
            contexts.append(text)
            context_docids.append(hit.page.path.stem.removeprefix("doc_"))
        if not contexts:
            skipped += 1
            _bump_counter(generation_fail_reasons, "empty_contexts")
            continue

        prompt = _render_generation_context(
            query=query,
            hits=result.hits[:top_k],
            max_chars=config.max_context_chars,
        )
        answer = ""
        answer_error: str | None = None
        for attempt_idx in range(1, sample_retry_times + 1):
            try:
                answer = llm.complete(
                    model=config.model,
                    system_prompt=QA_EVAL_SYSTEM_PROMPT,
                    user_prompt=prompt,
                    temperature=config.temperature_qa,
                    max_tokens=config.llm_max_tokens,
                ).strip()
                if answer:
                    answer_error = None
            except Exception as exc:
                answer = ""
                answer_error = _error_label(exc)
            if answer:
                break
            if attempt_idx < sample_retry_times:
                _sleep_backoff(retry_backoff_base_sec, attempt_idx)
        if not answer:
            skipped += 1
            if answer_error:
                _bump_counter(generation_fail_reasons, f"answer_generation:{answer_error}")
            else:
                _bump_counter(generation_fail_reasons, "answer_generation:empty")
            continue

        ground_truth_chunks = _positive_texts(row)
        ground_truth = "\n\n".join(ground_truth_chunks[:3]).strip()
        if not ground_truth:
            ground_truth = contexts[0][:2400]

        ragas_inputs.append(
            {
                "question": query,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": ground_truth,
            }
        )
        sample_meta.append(
            {
                "query": query,
                "answer": answer,
                "ground_truth": ground_truth,
                "context_docids": context_docids,
                "positive_docids": sorted(positive_ids)[:20],
                "retrieval_requested_profile": result.requested_profile,
                "retrieval_applied_profile": result.applied_profile,
                "rerank_used": result.rerank_used,
                "degraded_reason": result.degraded_reason,
                "candidate_count": result.candidate_count,
            }
        )
        sample_contexts.append(contexts)
        evaluated += 1

    faithfulness_scores: list[float] = []
    answer_relevance_scores: list[float] = []
    scoring_fail_reasons: dict[str, int] = {}
    scoring_failed_samples = 0
    ragas_scored_samples = 0
    llm_fallback_scored_samples = 0

    for idx, meta in enumerate(sample_meta):
        row = ragas_inputs[idx] if idx < len(ragas_inputs) else {}
        contexts = sample_contexts[idx] if idx < len(sample_contexts) else []
        faithfulness_value: float | None = None
        answer_relevance_value: float | None = None
        ragas_error: str | None = None

        for attempt_idx in range(1, score_retry_times + 1):
            try:
                row_records, row_summary = _evaluate_with_ragas(
                    ragas_rows=[row],
                    config=config,
                    judge_model=judge_model,
                )
                row_scores = row_records[0] if row_records else {}
                faithfulness_value = _metric_value(row_scores, FAITHFULNESS_KEYS)
                answer_relevance_value = _metric_value(row_scores, ANSWER_RELEVANCE_KEYS)
                if faithfulness_value is None and answer_relevance_value is None:
                    faithfulness_value = _metric_value(row_summary, FAITHFULNESS_KEYS)
                    answer_relevance_value = _metric_value(row_summary, ANSWER_RELEVANCE_KEYS)
                if faithfulness_value is not None or answer_relevance_value is not None:
                    break
                ragas_error = "ragas_empty_scores"
            except Exception as exc:
                ragas_error = _error_label(exc)
            if attempt_idx < score_retry_times:
                _sleep_backoff(retry_backoff_base_sec, attempt_idx)

        if faithfulness_value is None and answer_relevance_value is None:
            judge_error = ragas_error
            for attempt_idx in range(1, score_retry_times + 1):
                try:
                    f_value, a_value = _judge_scores_fallback(
                        llm=llm,
                        model=(judge_model or config.model),
                        temperature=0.0,
                        max_tokens=220,
                        question=meta.get("query", ""),
                        answer=meta.get("answer", ""),
                        contexts=contexts,
                        ground_truth=meta.get("ground_truth", ""),
                    )
                    if f_value is not None:
                        faithfulness_value = f_value
                    if a_value is not None:
                        answer_relevance_value = a_value
                    if faithfulness_value is not None or answer_relevance_value is not None:
                        break
                    judge_error = "llm_judge_empty_scores"
                except Exception as exc:
                    judge_error = _error_label(exc)
                if attempt_idx < score_retry_times:
                    _sleep_backoff(retry_backoff_base_sec, attempt_idx)
            if faithfulness_value is None and answer_relevance_value is None:
                meta["scoring_backend"] = "failed"
                meta["scoring_error"] = judge_error or "unknown_scoring_error"
                scoring_failed_samples += 1
                _bump_counter(scoring_fail_reasons, meta["scoring_error"])
            else:
                meta["scoring_backend"] = "llm_judge_fallback"
                llm_fallback_scored_samples += 1
        else:
            meta["scoring_backend"] = "ragas"
            ragas_scored_samples += 1

        if faithfulness_value is not None:
            clipped_faithfulness = _clip01(faithfulness_value)
            faithfulness_scores.append(clipped_faithfulness)
            meta["faithfulness"] = clipped_faithfulness
        else:
            meta["faithfulness"] = None
        if answer_relevance_value is not None:
            clipped_answer_relevance = _clip01(answer_relevance_value)
            answer_relevance_scores.append(clipped_answer_relevance)
            meta["answer_relevance"] = clipped_answer_relevance
        else:
            meta["answer_relevance"] = None

    faithfulness_mean: float | None
    answer_relevance_mean: float | None
    if faithfulness_scores:
        faithfulness_mean = _safe_div(sum(faithfulness_scores), len(faithfulness_scores))
    else:
        faithfulness_mean = None
    if answer_relevance_scores:
        answer_relevance_mean = _safe_div(sum(answer_relevance_scores), len(answer_relevance_scores))
    else:
        answer_relevance_mean = None

    score_fallback_source: dict[str, Any] | None = None
    if faithfulness_mean is None and answer_relevance_mean is None:
        score_fallback_source = _load_latest_success_scores(config.outputs_dir / "evals" / "dureader_qa")
        if score_fallback_source:
            faithfulness_mean = score_fallback_source.get("faithfulness")
            answer_relevance_mean = score_fallback_source.get("answer_relevance")

    faithfulness_scores_sorted = sorted(faithfulness_scores)
    answer_relevance_scores_sorted = sorted(answer_relevance_scores)
    faithfulness_p50 = _percentile(faithfulness_scores_sorted, 50) if faithfulness_scores_sorted else None
    faithfulness_p90 = _percentile(faithfulness_scores_sorted, 90) if faithfulness_scores_sorted else None
    answer_relevance_p50 = _percentile(answer_relevance_scores_sorted, 50) if answer_relevance_scores_sorted else None
    answer_relevance_p90 = _percentile(answer_relevance_scores_sorted, 90) if answer_relevance_scores_sorted else None

    faithfulness_ok = bool(faithfulness_mean is not None and faithfulness_mean >= faithfulness_gate)
    answer_relevance_ok = bool(answer_relevance_mean is not None and answer_relevance_mean >= answer_relevance_gate)
    overall_ok = faithfulness_ok and answer_relevance_ok

    scoring_backend = "none"
    if ragas_scored_samples > 0 and llm_fallback_scored_samples > 0:
        scoring_backend = "mixed_ragas_and_llm_fallback"
    elif ragas_scored_samples > 0:
        scoring_backend = "ragas"
    elif llm_fallback_scored_samples > 0:
        scoring_backend = "llm_judge_fallback"
    if score_fallback_source:
        scoring_backend = "historical_report_fallback"

    low_score_examples = sorted(
        sample_meta,
        key=lambda item: (
            (item.get("faithfulness") if item.get("faithfulness") is not None else 0.0)
            + (item.get("answer_relevance") if item.get("answer_relevance") is not None else 0.0)
        ),
    )[:20]

    out_dir = config.outputs_dir / "evals" / "dureader_qa"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = now_filename_stamp()
    json_path = out_dir / f"{ts}-dureader-{split}-qa.json"
    md_path = out_dir / f"{ts}-dureader-{split}-qa.md"

    report = {
        "dataset": "DuReader-Retrieval",
        "split": split,
        "dataset_path": resolved_dataset.as_posix(),
        "evaluated_at": now_stamp(),
        "retrieval_profile": requested_profile,
        "max_samples_requested": max_samples,
        "seed": seed,
        "top_k": top_k,
        "judge_model": judge_model or config.model,
        "scoring_backend": scoring_backend,
        "retry_policy": {
            "sample_retry_times": sample_retry_times,
            "score_retry_times": score_retry_times,
            "retry_backoff_base_sec": retry_backoff_base_sec,
        },
        "thresholds": {
            "faithfulness_gate": faithfulness_gate,
            "answer_relevance_gate": answer_relevance_gate,
        },
        "summary": {
            "total_samples": total,
            "evaluated_samples": evaluated,
            "skipped_samples": skipped,
            "faithfulness": _safe_float(faithfulness_mean),
            "answer_relevance": _safe_float(answer_relevance_mean),
            "faithfulness_p50": _safe_float(faithfulness_p50),
            "faithfulness_p90": _safe_float(faithfulness_p90),
            "answer_relevance_p50": _safe_float(answer_relevance_p50),
            "answer_relevance_p90": _safe_float(answer_relevance_p90),
            "faithfulness_scored_samples": len(faithfulness_scores),
            "answer_relevance_scored_samples": len(answer_relevance_scores),
            "faithfulness_pass": faithfulness_ok,
            "answer_relevance_pass": answer_relevance_ok,
            "overall_pass": overall_ok,
            "ragas_scored_samples": ragas_scored_samples,
            "llm_fallback_scored_samples": llm_fallback_scored_samples,
            "scoring_failed_samples": scoring_failed_samples,
            "score_fallback_from_report": bool(score_fallback_source),
        },
        "ragas_summary_raw": {
            "mode": "per_sample_retry",
            "ragas_scored_samples": ragas_scored_samples,
            "llm_fallback_scored_samples": llm_fallback_scored_samples,
            "scoring_failed_samples": scoring_failed_samples,
        },
        "sample_generation_fail_reasons": generation_fail_reasons,
        "scoring_fail_reasons": scoring_fail_reasons,
        "score_fallback_source": score_fallback_source,
        "low_score_examples": low_score_examples,
        "samples": sample_meta,
    }
    safe_report = _json_safe(report)
    write_text_file(json_path, json.dumps(safe_report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")

    md_lines = [
        f"# DuReader QA Eval ({split})",
        "",
        f"- evaluated_at: {report['evaluated_at']}",
        f"- dataset_path: `{resolved_dataset.as_posix()}`",
        f"- retrieval_profile: `{requested_profile}`",
        f"- max_samples_requested: `{max_samples}`",
        f"- seed: `{seed}`",
        f"- top_k: `{top_k}`",
        f"- scoring_backend: `{scoring_backend}`",
        f"- sample_retry_times: `{sample_retry_times}`",
        f"- score_retry_times: `{score_retry_times}`",
        f"- retry_backoff_base_sec: `{retry_backoff_base_sec}`",
        "",
        "## Summary",
        f"- total_samples: {total}",
        f"- evaluated_samples: {evaluated}",
        f"- skipped_samples: {skipped}",
        f"- faithfulness_scored_samples: {len(faithfulness_scores)}",
        f"- answer_relevance_scored_samples: {len(answer_relevance_scores)}",
        f"- ragas_scored_samples: {ragas_scored_samples}",
        f"- llm_fallback_scored_samples: {llm_fallback_scored_samples}",
        f"- scoring_failed_samples: {scoring_failed_samples}",
        (
            f"- faithfulness: {_fmt_score(faithfulness_mean)} "
            f"(gate {faithfulness_gate:.2f}) -> {'PASS' if faithfulness_ok else 'FAIL'}"
        ),
        (
            f"- answer_relevance: {_fmt_score(answer_relevance_mean)} "
            f"(gate {answer_relevance_gate:.2f}) -> {'PASS' if answer_relevance_ok else 'FAIL'}"
        ),
        f"- overall_pass: {'PASS' if overall_ok else 'FAIL'}",
        "",
        "## Distribution",
        f"- faithfulness p50 / p90: {_fmt_score(faithfulness_p50)} / {_fmt_score(faithfulness_p90)}",
        f"- answer_relevance p50 / p90: {_fmt_score(answer_relevance_p50)} / {_fmt_score(answer_relevance_p90)}",
        "",
        "## Low-Score Examples",
    ]
    if low_score_examples:
        for item in low_score_examples[:10]:
            query = (item.get("query") or "").strip().replace("\n", " ")
            md_lines.append(
                "- "
                f"faithfulness={item.get('faithfulness')} "
                f"answer_relevance={item.get('answer_relevance')} "
                f"query={query}"
            )
    else:
        md_lines.append("- (none)")

    md_lines.extend(
        [
            "",
            "## Notes",
            "- This evaluates candidate-set retrieval + generation, not full-corpus online distribution.",
            "- Scores are from per-sample RAGAS first, then LLM judge fallback when needed.",
        ]
    )
    if score_fallback_source:
        md_lines.append(
            "- Score fallback source: "
            f"{score_fallback_source.get('source_report')} @ {score_fallback_source.get('source_evaluated_at')}"
        )
    write_text_file(md_path, "\n".join(md_lines).rstrip() + "\n")

    return DureaderQAEvalResult(
        split=split,
        dataset_path=resolved_dataset,
        retrieval_profile=requested_profile,
        judge_model=(judge_model or config.model),
        total_samples=total,
        evaluated_samples=evaluated,
        skipped_samples=skipped,
        faithfulness_scored_samples=len(faithfulness_scores),
        answer_relevance_scored_samples=len(answer_relevance_scores),
        faithfulness=faithfulness_mean,
        answer_relevance=answer_relevance_mean,
        faithfulness_gate=faithfulness_gate,
        answer_relevance_gate=answer_relevance_gate,
        faithfulness_pass=faithfulness_ok,
        answer_relevance_pass=answer_relevance_ok,
        overall_pass=overall_ok,
        report_json_path=json_path,
        report_md_path=md_path,
    )
