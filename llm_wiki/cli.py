from __future__ import annotations

import argparse
import sys

from .compiler import build_index, compile_raw_to_wiki
from .config import AppConfig, load_config
from .dashboard_api import run_dashboard
from .eval_dureader import run_dureader_retrieval_eval
from .eval_dureader_qa import run_dureader_qa_eval
from .ingest import ingest_sources
from .io_utils import ensure_workspace
from .llm import LLMClient
from .qa import ask_wiki
from .search import TavilyClient, save_search_to_raw


def _configure_utf8_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm_wiki",
        description="LLM Wiki workflow: compile knowledge, then answer from wiki.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create raw/wiki/outputs directories.")

    p_compile = sub.add_parser("compile", help="Compile raw sources into wiki pages.")
    p_compile.add_argument("--max-docs", type=int, default=None, help="Only compile first N docs.")
    p_compile.add_argument("--force", action="store_true", help="Recompile even if page exists.")

    p_index = sub.add_parser("build-index", help="Rebuild wiki index and knowledge map.")

    p_ask = sub.add_parser("ask", help="Ask question from wiki knowledge.")
    p_ask.add_argument("question", help="Question text")
    p_ask.add_argument("-k", "--top-k", type=int, default=6, help="How many pages to retrieve.")
    p_ask.add_argument("--promote", action="store_true", help="Save answer into wiki/qa/")
    p_ask.add_argument(
        "--retrieval-profile",
        choices=["baseline", "hybrid_no_rerank", "hybrid_rerank"],
        default=None,
        help="Retriever profile override. Default uses RETRIEVAL_PROFILE from env.",
    )

    p_search = sub.add_parser("search", help="Search web via Tavily and save results into raw/web.")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--max-results", type=int, default=5, help="How many web results to fetch.")
    p_search.add_argument(
        "--compile",
        action="store_true",
        help="After saving search results to raw/, compile wiki and rebuild index.",
    )

    p_ingest = sub.add_parser(
        "ingest",
        help="Ingest multi-format files into raw/ingested markdown (pdf/docx/pptx/image/audio/json/md/txt...).",
    )
    p_ingest.add_argument("inputs", nargs="+", help="Input files, directories, or glob patterns.")
    p_ingest.add_argument("--max-files", type=int, default=None, help="Only ingest first N matched files.")
    p_ingest.add_argument("--force", action="store_true", help="Re-ingest even if target markdown exists.")
    p_ingest.add_argument(
        "--compile",
        action="store_true",
        help="After ingest, run compile and rebuild index.",
    )

    p_dashboard = sub.add_parser("dashboard", help="Run web dashboard for all operations.")
    p_dashboard.add_argument("--host", default="127.0.0.1", help="Dashboard host.")
    p_dashboard.add_argument("--port", type=int, default=8787, help="Dashboard port.")
    p_dashboard.add_argument("--reload", action="store_true", help="Enable auto-reload for development.")

    p_eval = sub.add_parser("eval-dureader", help="Evaluate retriever on DuReader-Retrieval candidate ranking set.")
    p_eval.add_argument("--split", choices=["dev", "train"], default="dev", help="Dataset split.")
    p_eval.add_argument(
        "--data-dir",
        default="raw/eval_data/dureader",
        help="Where downloaded dataset files are stored.",
    )
    p_eval.add_argument(
        "--dataset-path",
        default=None,
        help="Optional local dataset path (.jsonl or .jsonl.gz). If set, skip download.",
    )
    p_eval.add_argument(
        "--max-samples",
        type=int,
        default=1000,
        help="Evaluate first N samples (<=0 means all).",
    )
    p_eval.add_argument(
        "--retrieval-profile",
        choices=["baseline", "hybrid_no_rerank", "hybrid_rerank"],
        default=None,
        help="Retriever profile override. Default uses RETRIEVAL_PROFILE from env.",
    )
    p_eval.add_argument(
        "--ablation",
        action="store_true",
        help="Run baseline + hybrid_no_rerank + hybrid_rerank and compare in one report.",
    )
    p_eval.add_argument("--refresh", action="store_true", help="Force re-download split file.")
    p_eval.add_argument("--timeout", type=int, default=120, help="Download timeout in seconds.")

    p_eval_qa = sub.add_parser(
        "eval-dureader-qa",
        help="Evaluate QA quality (Faithfulness + Answer Relevance) on DuReader-Retrieval samples.",
    )
    p_eval_qa.add_argument("--split", choices=["dev", "train"], default="dev", help="Dataset split.")
    p_eval_qa.add_argument(
        "--data-dir",
        default="raw/eval_data/dureader",
        help="Where downloaded dataset files are stored.",
    )
    p_eval_qa.add_argument(
        "--dataset-path",
        default=None,
        help="Optional local dataset path (.jsonl or .jsonl.gz). If set, skip download.",
    )
    p_eval_qa.add_argument(
        "--max-samples",
        type=int,
        default=200,
        help="Evaluate up to N samples (<=0 means all).",
    )
    p_eval_qa.add_argument(
        "--retrieval-profile",
        choices=["baseline", "hybrid_no_rerank", "hybrid_rerank"],
        default="hybrid_rerank",
        help="Retriever profile used for QA context generation.",
    )
    p_eval_qa.add_argument("-k", "--top-k", type=int, default=6, help="How many retrieved contexts per sample.")
    p_eval_qa.add_argument("--seed", type=int, default=42, help="Random seed when sampling.")
    p_eval_qa.add_argument(
        "--judge-model",
        default=None,
        help="Optional model override for RAGAS judging. Default uses MODEL from env.",
    )
    p_eval_qa.add_argument(
        "--faithfulness-gate",
        type=float,
        default=0.85,
        help="PASS threshold for Faithfulness.",
    )
    p_eval_qa.add_argument(
        "--answer-relevance-gate",
        type=float,
        default=0.80,
        help="PASS threshold for Answer Relevance.",
    )
    p_eval_qa.add_argument(
        "--sample-retry-times",
        type=int,
        default=3,
        help="Retries for per-sample answer generation failures.",
    )
    p_eval_qa.add_argument(
        "--score-retry-times",
        type=int,
        default=3,
        help="Retries for per-sample scoring failures (RAGAS and judge fallback).",
    )
    p_eval_qa.add_argument(
        "--retry-backoff-base-sec",
        type=float,
        default=1.0,
        help="Base seconds for exponential backoff between retries.",
    )
    p_eval_qa.add_argument("--refresh", action="store_true", help="Force re-download split file.")
    p_eval_qa.add_argument("--timeout", type=int, default=120, help="Download timeout in seconds.")

    return parser


def _new_llm_client(config: AppConfig) -> LLMClient:
    if config.llm_provider.lower() != "openai":
        raise SystemExit(f"Unsupported LLM_PROVIDER={config.llm_provider}. Only 'openai' is supported.")
    try:
        return LLMClient(api_key=config.openai_api_key, base_url=config.openai_base_url)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def _new_tavily_client(config: AppConfig) -> TavilyClient:
    try:
        return TavilyClient(api_key=config.tavily_api_key, base_url=config.tavily_base_url)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    args = _build_parser().parse_args(argv)
    config = load_config()
    ensure_workspace(config.raw_dir, config.wiki_dir, config.outputs_dir)

    if args.command == "init":
        print(f"Workspace ready: {config.raw_dir}, {config.wiki_dir}, {config.outputs_dir}")
        return 0

    if args.command == "compile":
        llm = _new_llm_client(config)
        pages = compile_raw_to_wiki(
            config,
            llm=llm,
            max_docs=args.max_docs,
            force=args.force,
        )
        files = build_index(config, llm=llm)
        print(f"Compiled pages: {len(pages)}")
        print("Updated:")
        for path in files:
            print(f"- {path.as_posix()}")
        return 0

    if args.command == "build-index":
        llm = _new_llm_client(config)
        files = build_index(config, llm=llm)
        print("Updated:")
        for path in files:
            print(f"- {path.as_posix()}")
        return 0

    if args.command == "ask":
        llm = _new_llm_client(config)
        result = ask_wiki(
            config,
            question=args.question.strip(),
            llm=llm,
            top_k=args.top_k,
            promote=args.promote,
            retrieval_profile=args.retrieval_profile,
        )
        print(f"Saved output: {result.output_path.as_posix()}")
        print(f"Retrieval profile: requested={result.retrieval_requested_profile}, applied={result.retrieval_applied_profile}")
        if result.retrieval_degraded_reason:
            print(f"Retrieval degraded: {result.retrieval_degraded_reason}")
        print("Used pages:")
        for path in result.used_pages:
            print(f"- {path.as_posix()}")
        print("\nAnswer:\n")
        print(result.answer)
        return 0

    if args.command == "search":
        client = _new_tavily_client(config)
        result = client.search(query=args.query.strip(), max_results=args.max_results)
        capture_path = save_search_to_raw(config.raw_dir, query=args.query.strip(), result=result)
        print(f"Saved search capture: {capture_path.as_posix()}")
        print(f"Fetched results: {len(result.hits)}")

        if args.compile:
            llm = _new_llm_client(config)
            pages = compile_raw_to_wiki(config, llm=llm, force=False)
            files = build_index(config, llm=llm)
            print(f"Compiled pages: {len(pages)}")
            print("Updated:")
            for path in files:
                print(f"- {path.as_posix()}")
        return 0

    if args.command == "ingest":
        if args.compile:
            llm: LLMClient | None = _new_llm_client(config)
        else:
            try:
                llm = _new_llm_client(config)
            except SystemExit as exc:
                llm = None
                print(
                    "[warn] LLM client unavailable; image/OCR/ASR extraction may fail. "
                    f"Details: {exc}",
                    file=sys.stderr,
                )
        summary = ingest_sources(
            config,
            llm=llm,
            inputs=args.inputs,
            force=args.force,
            max_files=args.max_files,
        )
        print(f"Ingested: {len(summary.ingested)}")
        print(f"Skipped existing: {len(summary.skipped_existing)}")
        print(f"Skipped unsupported: {len(summary.skipped_unsupported)}")
        print(f"Errors: {len(summary.errors)}")

        if summary.ingested:
            print("Created:")
            for item in summary.ingested:
                print(f"- {item.output_path.as_posix()} ({item.source_type} via {item.extractor})")

        if summary.errors:
            print("\nIngest errors:")
            for err in summary.errors:
                print(f"- {err}")

        if args.compile:
            if llm is None:
                llm = _new_llm_client(config)
            pages = compile_raw_to_wiki(config, llm=llm, force=False)
            files = build_index(config, llm=llm)
            print(f"\nCompiled pages: {len(pages)}")
            print("Updated:")
            for path in files:
                print(f"- {path.as_posix()}")
        return 0

    if args.command == "dashboard":
        print(f"Starting dashboard at http://{args.host}:{args.port}")
        run_dashboard(host=args.host, port=args.port, reload=args.reload)
        return 0

    if args.command == "eval-dureader":
        from pathlib import Path

        result = run_dureader_retrieval_eval(
            config,
            split=args.split,
            data_dir=Path(args.data_dir),
            dataset_path=Path(args.dataset_path) if args.dataset_path else None,
            max_samples=None if args.max_samples <= 0 else args.max_samples,
            refresh=args.refresh,
            timeout_sec=args.timeout,
            retrieval_profile=args.retrieval_profile,
            ablation=args.ablation,
        )
        print(f"DuReader-Retrieval ({result.split}) evaluation done.")
        print(f"- Retrieval profile: {result.retrieval_profile}")
        print(f"- Dataset: {result.dataset_path.as_posix()}")
        print(f"- Total samples: {result.total_samples}")
        print(f"- Evaluated: {result.evaluated_samples}")
        print(f"- Skipped: {result.skipped_samples}")
        print(f"- Mean candidates/query: {result.mean_candidates:.2f}")
        print(f"- MRR@10: {result.mrr_at_10:.4f}")
        print(f"- Recall@1: {result.recall_at_1:.4f}")
        print(f"- Recall@5: {result.recall_at_5:.4f}")
        print(f"- Recall@10: {result.recall_at_10:.4f}")
        print(f"- Recall@20: {result.recall_at_20:.4f}")
        print(f"- Recall@50: {result.recall_at_50:.4f}")
        print(f"- Rerank used ratio: {result.rerank_used_ratio:.4f}")
        print(f"- Degraded ratio: {result.degraded_ratio:.4f}")
        if args.ablation:
            print("- Profiles:")
            for profile_name, metrics in result.profile_results.items():
                print(
                    "  "
                    f"{profile_name}: MRR@10={metrics.get('mrr@10', 0.0):.4f}, "
                    f"R@1={metrics.get('recall@1', 0.0):.4f}, "
                    f"R@10={metrics.get('recall@10', 0.0):.4f}"
                )
        print(f"- JSON report: {result.report_json_path.as_posix()}")
        print(f"- Markdown report: {result.report_md_path.as_posix()}")
        return 0

    if args.command == "eval-dureader-qa":
        from pathlib import Path

        def _fmt_metric(value: float | None) -> str:
            if value is None:
                return "n/a"
            return f"{value:.4f}"

        result = run_dureader_qa_eval(
            config,
            split=args.split,
            data_dir=Path(args.data_dir),
            dataset_path=Path(args.dataset_path) if args.dataset_path else None,
            max_samples=None if args.max_samples <= 0 else args.max_samples,
            refresh=args.refresh,
            timeout_sec=args.timeout,
            retrieval_profile=args.retrieval_profile,
            top_k=args.top_k,
            seed=args.seed,
            judge_model=args.judge_model,
            faithfulness_gate=args.faithfulness_gate,
            answer_relevance_gate=args.answer_relevance_gate,
            sample_retry_times=args.sample_retry_times,
            score_retry_times=args.score_retry_times,
            retry_backoff_base_sec=args.retry_backoff_base_sec,
        )
        print(f"DuReader QA ({result.split}) evaluation done.")
        print(f"- Retrieval profile: {result.retrieval_profile}")
        print(f"- Judge model: {result.judge_model}")
        print(f"- Dataset: {result.dataset_path.as_posix()}")
        print(f"- Total samples: {result.total_samples}")
        print(f"- Evaluated: {result.evaluated_samples}")
        print(f"- Skipped: {result.skipped_samples}")
        print(f"- Faithfulness scored samples: {result.faithfulness_scored_samples}")
        print(f"- Answer Relevance scored samples: {result.answer_relevance_scored_samples}")
        print(
            f"- Faithfulness: {_fmt_metric(result.faithfulness)} "
            f"(gate {result.faithfulness_gate:.2f}) -> {'PASS' if result.faithfulness_pass else 'FAIL'}"
        )
        print(
            f"- Answer Relevance: {_fmt_metric(result.answer_relevance)} "
            f"(gate {result.answer_relevance_gate:.2f}) -> {'PASS' if result.answer_relevance_pass else 'FAIL'}"
        )
        print(f"- Overall: {'PASS' if result.overall_pass else 'FAIL'}")
        print(f"- JSON report: {result.report_json_path.as_posix()}")
        print(f"- Markdown report: {result.report_md_path.as_posix()}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
