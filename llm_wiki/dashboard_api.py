from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock, Thread
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .compiler import build_index, compile_raw_to_wiki
from .config import AppConfig, load_config
from .ingest import ingest_sources, normalize_source_inputs, resolve_sources
from .io_utils import ensure_workspace
from .llm import LLMClient
from .qa import ask_wiki
from .search import TavilyClient, save_search_to_raw


def _format_dt(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _collect_files(root: Path, pattern: str = "*") -> list[Path]:
    if not root.exists():
        return []
    return sorted((p for p in root.rglob(pattern) if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)


def _new_llm(config: AppConfig) -> LLMClient:
    return LLMClient(api_key=config.openai_api_key, base_url=config.openai_base_url)


def _new_tavily(config: AppConfig) -> TavilyClient:
    return TavilyClient(api_key=config.tavily_api_key, base_url=config.tavily_base_url)


@dataclass
class JobState:
    id: str
    group_id: str
    operation: str
    kind: str
    label_cn: str
    parent_id: str | None = None
    stage: str = "queued"
    status: str = "queued"
    progress: int = 0
    message: str = "已排队"
    summary: str = ""
    next_action: str = ""
    result_preview: str = ""
    created_at: str = field(default_factory=_iso_now)
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
    updated_at: str = field(default_factory=_iso_now)
    logs: list[str] = field(default_factory=list)
    result: dict | None = None
    error: str | None = None


@dataclass
class GroupState:
    id: str
    kind: str
    label_cn: str
    created_at: str = field(default_factory=_iso_now)
    updated_at: str = field(default_factory=_iso_now)
    summary: str = ""
    next_action: str = ""


class JobExecutionError(RuntimeError):
    def __init__(self, message: str, *, result: dict | None = None) -> None:
        super().__init__(message)
        self.result = result or {}


class CompileReq(BaseModel):
    max_docs: int | None = None
    force: bool = False


class AskReq(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = 6
    promote: bool = False
    retrieval_profile: str | None = None


class SearchReq(BaseModel):
    query: str = Field(min_length=1)
    max_results: int = 5
    compile: bool = False


class IngestReq(BaseModel):
    inputs: list[str] = Field(min_length=1)
    force: bool = False
    max_files: int | None = None
    compile: bool = False
    strict: bool = True


def create_app() -> FastAPI:
    config = load_config()
    ensure_workspace(config.raw_dir, config.wiki_dir, config.outputs_dir)
    cwd = Path.cwd()
    static_dir = Path(__file__).parent / "dashboard_static"

    app = FastAPI(title="LLM Wiki Dashboard", version="0.3.0")
    if static_dir.exists():
        app.mount("/assets", StaticFiles(directory=static_dir), name="assets")

    jobs: dict[str, JobState] = {}
    groups: dict[str, GroupState] = {}
    group_members: dict[str, list[str]] = defaultdict(list)
    jobs_lock = Lock()
    max_jobs = 300

    op_label_map = {
        "init": "初始化工作区",
        "compile": "编译知识",
        "build-index": "重建索引",
        "ask": "向知识库提问",
        "search": "检索资料",
        "ingest": "资料入库",
    }
    op_next_map = {
        "init": "可以开始资料入库",
        "compile": "可以开始提问",
        "build-index": "可以开始提问",
        "ask": "查看问答结果",
        "search": "可选择编译新资料",
        "ingest": "建议继续编译索引",
    }

    def _serialize_job(job: JobState) -> dict:
        return asdict(job)

    def _touch_group(group_id: str, *, summary: str | None = None, next_action: str | None = None) -> None:
        group = groups.get(group_id)
        if not group:
            return
        group.updated_at = _iso_now()
        if summary is not None:
            group.summary = summary
        if next_action is not None:
            group.next_action = next_action

    def _trim_jobs() -> None:
        if len(jobs) <= max_jobs:
            return
        ordered = sorted(jobs.values(), key=lambda x: x.updated_at)
        for item in ordered:
            if len(jobs) <= max_jobs:
                break
            if item.status in {"completed", "error"}:
                jobs.pop(item.id, None)
                if item.group_id in group_members:
                    group_members[item.group_id] = [jid for jid in group_members[item.group_id] if jid != item.id]

    def _update_job(
        self_id: str,
        *,
        status: str | None = None,
        progress: int | None = None,
        message: str | None = None,
        stage: str | None = None,
        summary: str | None = None,
        next_action: str | None = None,
        result_preview: str | None = None,
        result: dict | None = None,
        error: str | None = None,
        log: str | None = None,
    ) -> None:
        with jobs_lock:
            job = jobs.get(self_id)
            if not job:
                return
            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = max(0, min(100, int(progress)))
            if message is not None:
                job.message = message
            if stage is not None:
                job.stage = stage
            if summary is not None:
                job.summary = summary
            if next_action is not None:
                job.next_action = next_action
            if result_preview is not None:
                job.result_preview = result_preview
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            if log:
                line = f"[{_format_dt(datetime.now().timestamp())}] {log}"
                job.logs.append(line)
                if len(job.logs) > 120:
                    job.logs = job.logs[-120:]
            job.updated_at = _iso_now()
            _touch_group(job.group_id, summary=job.summary or None, next_action=job.next_action or None)
            _trim_jobs()

    def _create_group(kind: str, label_cn: str, next_action: str) -> str:
        group_id = uuid4().hex
        with jobs_lock:
            groups[group_id] = GroupState(id=group_id, kind=kind, label_cn=label_cn, next_action=next_action)
        return group_id

    def _start_job(
        *,
        operation: str,
        kind: str,
        group_id: str,
        parent_id: str | None,
        label_cn: str,
        default_next_action: str,
        runner: Callable[[Callable[[int, str, str | None], None]], dict],
    ) -> str:
        job_id = uuid4().hex
        initial = JobState(
            id=job_id,
            group_id=group_id,
            operation=operation,
            kind=kind,
            label_cn=label_cn,
            parent_id=parent_id,
            next_action=default_next_action,
        )
        with jobs_lock:
            jobs[job_id] = initial
            group_members[group_id].append(job_id)
            _touch_group(group_id, next_action=default_next_action)
            _trim_jobs()

        def _run() -> None:
            now = datetime.now()
            _update_job(
                job_id,
                status="running",
                stage="running",
                progress=1,
                message="任务已启动",
                summary="任务执行中",
                log="任务已启动",
            )
            with jobs_lock:
                job = jobs.get(job_id)
                if job:
                    job.started_at = _iso_now()

            def _progress(percent: int, text: str, stage: str | None = None) -> None:
                _update_job(
                    job_id,
                    progress=percent,
                    message=text,
                    stage=stage,
                    summary=text,
                    log=text,
                )

            try:
                payload = runner(_progress)
                preview = ""
                if isinstance(payload, dict):
                    if payload.get("answer"):
                        ans = str(payload.get("answer", "")).strip().replace("\n", " ")
                        preview = ans[:180]
                    elif payload.get("output_path"):
                        preview = f"输出: {payload.get('output_path')}"
                    elif payload.get("capture_path"):
                        preview = f"检索结果: {payload.get('capture_path')}"
                _update_job(
                    job_id,
                    status="completed",
                    stage="completed",
                    progress=100,
                    message="已完成",
                    summary="任务已完成",
                    result=payload,
                    result_preview=preview,
                    log="任务已完成",
                )
            except JobExecutionError as exc:
                _update_job(
                    job_id,
                    status="error",
                    stage="error",
                    progress=100,
                    message=f"失败: {exc}",
                    summary=str(exc),
                    error=str(exc),
                    result=exc.result,
                    log=f"失败: {exc}",
                )
            except Exception as exc:  # noqa: BLE001
                _update_job(
                    job_id,
                    status="error",
                    stage="error",
                    progress=100,
                    message=f"失败: {exc}",
                    summary=str(exc),
                    error=str(exc),
                    log=f"失败: {exc}",
                )
            finally:
                end = datetime.now()
                with jobs_lock:
                    job = jobs.get(job_id)
                    if job:
                        job.finished_at = _iso_now()
                        job.duration_ms = int((end - now).total_seconds() * 1000)
                        job.updated_at = _iso_now()
                        _touch_group(job.group_id)

        Thread(target=_run, daemon=True).start()
        return job_id

    def _get_job(job_id: str) -> dict:
        with jobs_lock:
            job = jobs.get(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found.")
            return _serialize_job(job)

    def _group_jobs_snapshot(group_id: str) -> list[JobState]:
        ids = group_members.get(group_id, [])
        return [jobs[jid] for jid in ids if jid in jobs]

    def _group_summary(group_id: str) -> dict:
        group = groups.get(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Job group not found.")
        members = _group_jobs_snapshot(group_id)
        total = len(members)
        running = sum(1 for j in members if j.status in {"queued", "running"})
        failed = sum(1 for j in members if j.status == "error")
        completed = sum(1 for j in members if j.status == "completed")
        progress = 0 if total == 0 else int(sum(j.progress for j in members) / total)
        latest = sorted(members, key=lambda x: x.updated_at, reverse=True)
        latest_job = latest[0] if latest else None
        status = "idle"
        if running > 0:
            status = "running"
        elif failed > 0:
            status = "error"
        elif completed > 0 and completed == total:
            status = "completed"
        return {
            "id": group.id,
            "kind": group.kind,
            "label_cn": group.label_cn,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "status": status,
            "progress": progress,
            "summary": latest_job.summary if latest_job and latest_job.summary else group.summary,
            "next_action": latest_job.next_action if latest_job and latest_job.next_action else group.next_action,
            "counts": {
                "total": total,
                "running": running,
                "failed": failed,
                "completed": completed,
            },
            "latest_job_id": latest_job.id if latest_job else None,
            "latest_message": latest_job.message if latest_job else "",
        }

    def _serialize_recent(paths: list[Path], limit: int = 8) -> list[dict]:
        data: list[dict] = []
        for p in paths[:limit]:
            stat = p.stat()
            data.append(
                {
                    "name": p.name,
                    "path": p.as_posix(),
                    "mtime": _format_dt(stat.st_mtime),
                    "size": stat.st_size,
                }
            )
        return data

    @app.get("/")
    def home() -> Response:
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse(
            content=(
                "<!doctype html><html><head><meta charset='utf-8'>"
                "<title>LLM Wiki Dashboard</title></head>"
                "<body><h1>LLM Wiki Dashboard</h1><p>前端页面暂未生成，请先准备 dashboard_static/index.html。</p></body></html>"
            )
        )

    @app.get("/api/overview")
    def overview() -> dict:
        raw_files = _collect_files(config.raw_dir)
        ingested_files = _collect_files(config.raw_dir / "ingested", "*.md")
        web_files = _collect_files(config.raw_dir / "web", "*.md")
        wiki_sources = _collect_files(config.wiki_dir / "sources", "*.md")
        wiki_qa = _collect_files(config.wiki_dir / "qa", "*.md")
        outputs = _collect_files(config.outputs_dir, "*.md")
        index_path = config.wiki_dir / "index.md"
        knowledge_map = config.wiki_dir / "knowledge_map.md"
        return {
            "workspace": cwd.as_posix(),
            "model": config.model,
            "vision_model": config.vision_model,
            "asr_model": config.asr_model,
            "retrieval_profile": config.retrieval_profile,
            "counts": {
                "raw_total": len(raw_files),
                "raw_ingested": len(ingested_files),
                "raw_web": len(web_files),
                "wiki_sources": len(wiki_sources),
                "wiki_qa": len(wiki_qa),
                "outputs": len(outputs),
            },
            "status": {
                "index_updated": _format_dt(index_path.stat().st_mtime) if index_path.exists() else "N/A",
                "knowledge_map_updated": _format_dt(knowledge_map.stat().st_mtime) if knowledge_map.exists() else "N/A",
            },
            "recent": {
                "outputs": _serialize_recent(outputs),
                "wiki_sources": _serialize_recent(wiki_sources),
                "raw_ingested": _serialize_recent(ingested_files),
            },
        }

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict:
        return _get_job(job_id)

    @app.get("/api/jobs")
    def list_jobs(
        status: str | None = Query(default=None),
        kind: str | None = Query(default=None),
        group_id: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=300),
    ) -> dict:
        with jobs_lock:
            items = list(jobs.values())
        if status:
            items = [j for j in items if j.status == status]
        if kind:
            items = [j for j in items if j.kind == kind]
        if group_id:
            items = [j for j in items if j.group_id == group_id]
        items.sort(key=lambda x: x.updated_at, reverse=True)
        data = [_serialize_job(job) for job in items[:limit]]
        return {"items": data, "total": len(items)}

    @app.get("/api/job-groups")
    def list_job_groups(
        status: str | None = Query(default=None),
        kind: str | None = Query(default=None),
        limit: int = Query(default=30, ge=1, le=200),
    ) -> dict:
        with jobs_lock:
            group_ids = sorted(groups.keys(), key=lambda gid: groups[gid].updated_at, reverse=True)
            summaries = [_group_summary(gid) for gid in group_ids]
        if status:
            summaries = [g for g in summaries if g["status"] == status]
        if kind:
            summaries = [g for g in summaries if g["kind"] == kind]
        return {"items": summaries[:limit], "total": len(summaries)}

    @app.get("/api/job-groups/{group_id}")
    def get_job_group(group_id: str) -> dict:
        with jobs_lock:
            summary = _group_summary(group_id)
            jobs_in_group = _group_jobs_snapshot(group_id)
            jobs_in_group.sort(key=lambda x: x.updated_at, reverse=True)
            items = [_serialize_job(job) for job in jobs_in_group]
            primary = next((j for j in jobs_in_group if j.parent_id is None), jobs_in_group[0] if jobs_in_group else None)
        return {
            "group": summary,
            "primary_job": _serialize_job(primary) if primary else None,
            "jobs": items,
        }

    def _launch_operation(
        *,
        operation: str,
        kind: str,
        runner: Callable[[Callable[[int, str, str | None], None]], dict],
    ) -> dict:
        label = op_label_map.get(operation, operation)
        next_action = op_next_map.get(operation, "")
        group_id = _create_group(kind=kind, label_cn=label, next_action=next_action)
        job_id = _start_job(
            operation=operation,
            kind=kind,
            group_id=group_id,
            parent_id=None,
            label_cn=label,
            default_next_action=next_action,
            runner=runner,
        )
        return {"ok": True, "job_id": job_id, "job_group_id": group_id}

    @app.post("/api/init")
    def init_workspace() -> dict:
        def _runner(update: Callable[[int, str, str | None], None]) -> dict:
            update(20, "检查并创建目录", "prepare")
            ensure_workspace(config.raw_dir, config.wiki_dir, config.outputs_dir)
            update(100, "初始化完成", "completed")
            return {"message": "Workspace initialized"}

        return _launch_operation(operation="init", kind="admin", runner=_runner)

    @app.post("/api/compile")
    def compile_api(req: CompileReq) -> dict:
        def _runner(update: Callable[[int, str, str | None], None]) -> dict:
            llm = _new_llm(config)
            update(4, "准备编译", "prepare")

            def _compile_cb(current: int, total: int, message: str) -> None:
                pct = 5 + int((current / max(total, 1)) * 80)
                update(min(pct, 85), message, "compile")

            compiled = compile_raw_to_wiki(config, llm=llm, max_docs=req.max_docs, force=req.force, progress_cb=_compile_cb)
            update(86, "重建索引", "index")

            def _index_cb(current: int, total: int, message: str) -> None:
                pct = 86 + int((current / max(total, 1)) * 13)
                update(min(pct, 99), message, "index")

            updated = build_index(config, llm=llm, progress_cb=_index_cb)
            update(100, "编译完成", "completed")
            return {
                "compiled_count": len(compiled),
                "compiled_paths": [p.as_posix() for p in compiled],
                "updated_paths": [p.as_posix() for p in updated],
            }

        return _launch_operation(operation="compile", kind="compile", runner=_runner)

    @app.post("/api/build-index")
    def build_index_api() -> dict:
        def _runner(update: Callable[[int, str, str | None], None]) -> dict:
            llm = _new_llm(config)
            update(8, "准备重建索引", "prepare")

            def _index_cb(current: int, total: int, message: str) -> None:
                pct = 10 + int((current / max(total, 1)) * 88)
                update(min(pct, 99), message, "index")

            updated = build_index(config, llm=llm, progress_cb=_index_cb)
            update(100, "索引重建完成", "completed")
            return {"updated_paths": [p.as_posix() for p in updated]}

        return _launch_operation(operation="build-index", kind="index", runner=_runner)

    @app.post("/api/ask")
    def ask_api(req: AskReq) -> dict:
        def _runner(update: Callable[[int, str, str | None], None]) -> dict:
            llm = _new_llm(config)
            update(15, "准备问答上下文", "prepare")
            result = ask_wiki(
                config,
                llm=llm,
                question=req.question,
                top_k=req.top_k,
                promote=req.promote,
                retrieval_profile=req.retrieval_profile,
            )
            update(100, "回答已生成", "completed")
            return {
                "output_path": result.output_path.as_posix(),
                "used_pages": [p.as_posix() for p in result.used_pages],
                "answer": result.answer,
                "retrieval_requested_profile": result.retrieval_requested_profile,
                "retrieval_applied_profile": result.retrieval_applied_profile,
                "retrieval_degraded_reason": result.retrieval_degraded_reason,
            }

        return _launch_operation(operation="ask", kind="ask", runner=_runner)

    @app.post("/api/search")
    def search_api(req: SearchReq) -> dict:
        def _runner(update: Callable[[int, str, str | None], None]) -> dict:
            client = _new_tavily(config)
            update(8, "调用检索服务", "search")
            result = client.search(query=req.query, max_results=req.max_results)
            update(50, "保存检索结果", "search")
            capture = save_search_to_raw(config.raw_dir, query=req.query, result=result)
            payload: dict[str, object] = {
                "capture_path": capture.as_posix(),
                "result_count": len(result.hits),
            }
            if req.compile:
                llm = _new_llm(config)
                update(60, "编译新检索资料", "compile")

                def _compile_cb(current: int, total: int, message: str) -> None:
                    pct = 62 + int((current / max(total, 1)) * 28)
                    update(min(pct, 90), message, "compile")

                compiled = compile_raw_to_wiki(config, llm=llm, force=False, progress_cb=_compile_cb)

                def _index_cb(current: int, total: int, message: str) -> None:
                    pct = 90 + int((current / max(total, 1)) * 9)
                    update(min(pct, 99), message, "index")

                updated = build_index(config, llm=llm, progress_cb=_index_cb)
                payload["compiled_count"] = len(compiled)
                payload["updated_paths"] = [p.as_posix() for p in updated]
            update(100, "检索流程完成", "completed")
            return payload

        return _launch_operation(operation="search", kind="search", runner=_runner)

    @app.post("/api/ingest")
    def ingest_api(req: IngestReq) -> dict:
        normalized_inputs = normalize_source_inputs(req.inputs)
        resolved_inputs = resolve_sources(normalized_inputs, max_files=req.max_files)
        if not resolved_inputs:
            raise HTTPException(status_code=400, detail="没有解析到任何有效输入文件，请检查路径是否存在，或去掉首尾引号。")

        def _runner(update: Callable[[int, str, str | None], None]) -> dict:
            if req.compile:
                llm: LLMClient | None = _new_llm(config)
            else:
                try:
                    llm = _new_llm(config)
                except ValueError:
                    llm = None

            update(3, "准备入库输入", "prepare")

            def _ingest_cb(current: int, total: int, message: str) -> None:
                pct = 5 + int((current / max(total, 1)) * 68)
                update(min(pct, 73), message, "ingest")

            summary = ingest_sources(
                config,
                llm=llm,
                inputs=normalized_inputs,
                force=req.force,
                max_files=req.max_files,
                progress_cb=_ingest_cb,
            )
            payload: dict[str, object] = {
                "strict": req.strict,
                "ingested_count": len(summary.ingested),
                "skipped_existing": len(summary.skipped_existing),
                "skipped_unsupported": len(summary.skipped_unsupported),
                "errors": summary.errors,
                "created": [
                    {
                        "source_path": item.source_path.as_posix(),
                        "output_path": item.output_path.as_posix(),
                        "source_type": item.source_type,
                        "extractor": item.extractor,
                    }
                    for item in summary.ingested
                ],
            }

            if req.compile:
                update(75, "编译入库内容", "compile")

                def _compile_cb(current: int, total: int, message: str) -> None:
                    pct = 76 + int((current / max(total, 1)) * 18)
                    update(min(pct, 94), message, "compile")

                compiled = compile_raw_to_wiki(config, llm=llm, force=False, progress_cb=_compile_cb)

                def _index_cb(current: int, total: int, message: str) -> None:
                    pct = 94 + int((current / max(total, 1)) * 5)
                    update(min(pct, 99), message, "index")

                updated = build_index(config, llm=llm, progress_cb=_index_cb)
                payload["compiled_count"] = len(compiled)
                payload["updated_paths"] = [p.as_posix() for p in updated]

            if summary.errors:
                error_count = len(summary.errors)
                update(100, f"入库完成，但有 {error_count} 个错误", "completed")
                if req.strict:
                    raise JobExecutionError(
                        f"严格模式失败：存在 {error_count} 个错误",
                        result=payload,
                    )

            update(100, "入库完成", "completed")
            return payload

        return _launch_operation(operation="ingest", kind="ingest", runner=_runner)

    return app


def run_dashboard(host: str = "127.0.0.1", port: int = 8787, reload: bool = False) -> None:
    import uvicorn

    uvicorn.run("llm_wiki.dashboard_api:create_app", factory=True, host=host, port=port, reload=reload)
