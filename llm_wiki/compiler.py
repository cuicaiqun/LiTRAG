from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable

from .config import AppConfig
from .io_utils import (
    ensure_workspace,
    iter_text_files,
    now_stamp,
    read_text_file,
    safe_slug,
    write_text_file,
)
from .llm import LLMClient


COMPILE_SYSTEM_PROMPT = """You are a knowledge compiler.
Your job: convert one raw source into a reusable wiki page.

Output markdown with this structure:
# <Page Title>
## Summary
## Key Claims
## Concepts And Entities
## Contradictions Or Tensions
## Open Questions
## Practical Notes

Rules:
- Keep it specific and faithful to source text.
- If unsure, explicitly mark uncertainty.
- Prefer concise bullet points.
- Do not invent facts not implied by source."""


KNOWLEDGE_MAP_SYSTEM_PROMPT = """You are synthesizing a cross-document knowledge map.
Create markdown with:
# Knowledge Map
## Core Themes
## Important Connections
## Contradictions / Conflicts
## Missing Evidence
## Suggested Next Questions

Ground everything in provided wiki summaries only."""


COMPILE_PROMPT_VERSION = "2026-04-09-v1"
COMPILE_MANIFEST_FILE = ".compile_manifest.json"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 120


def _manifest_path(config: AppConfig) -> Path:
    return config.wiki_dir / COMPILE_MANIFEST_FILE


def _load_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    cleaned: dict[str, dict[str, str]] = {}
    for key, value in payload.items():
        if isinstance(key, str) and isinstance(value, dict):
            cleaned[key] = {str(k): str(v) for k, v in value.items()}
    return cleaned


def _save_manifest(path: Path, payload: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _extractor_version(raw_rel: Path, raw_text: str) -> str:
    if raw_rel.parts and raw_rel.parts[0] == "ingested":
        for line in raw_text.splitlines()[:40]:
            if line.lower().startswith("- extractor:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    return value
    return "raw_text_v1"


def _compile_fingerprint(raw_text: str, extractor_version: str) -> tuple[str, str]:
    file_hash = hashlib.sha1(raw_text.encode("utf-8")).hexdigest()
    base = f"{file_hash}|{extractor_version}|{COMPILE_PROMPT_VERSION}"
    fingerprint = hashlib.sha1(base.encode("utf-8")).hexdigest()
    return file_hash, fingerprint


def compile_raw_to_wiki(
    config: AppConfig,
    *,
    llm: LLMClient,
    max_docs: int | None = None,
    force: bool = False,
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> list[Path]:
    ensure_workspace(config.raw_dir, config.wiki_dir, config.outputs_dir)
    source_files = iter_text_files(config.raw_dir)
    if max_docs is not None:
        source_files = source_files[:max_docs]

    manifest_file = _manifest_path(config)
    manifest = _load_manifest(manifest_file)

    total = max(len(source_files), 1)
    if progress_cb:
        progress_cb(0, total, f"Scanning {len(source_files)} source files")

    written_pages: list[Path] = []
    for idx, raw_path in enumerate(source_files, start=1):
        raw_rel = raw_path.relative_to(config.raw_dir)
        slug = safe_slug(raw_rel.with_suffix("").as_posix().replace("/", "-"))
        target = config.wiki_dir / "sources" / f"{slug}.md"
        key = raw_rel.as_posix()

        if progress_cb:
            progress_cb(idx - 1, total, f"Compiling {key}")

        raw_text_full = read_text_file(raw_path).strip()
        if not raw_text_full:
            if progress_cb:
                progress_cb(idx, total, f"Skipped empty file {key}")
            continue

        extractor_ver = _extractor_version(raw_rel, raw_text_full)
        file_hash, fingerprint = _compile_fingerprint(raw_text_full, extractor_ver)

        cached = manifest.get(key, {})
        if target.exists() and not force and cached.get("fingerprint") == fingerprint:
            if progress_cb:
                progress_cb(idx, total, f"Skipped unchanged {key}")
            continue

        raw_text = raw_text_full[: config.max_source_chars]
        user_prompt = (
            f"Source path: {key}\n"
            "Compile the following source into a wiki page.\n\n"
            f"{raw_text}"
        )
        compiled_body = llm.complete(
            model=config.model,
            system_prompt=COMPILE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=config.temperature_compile,
            max_tokens=config.llm_max_tokens,
        )

        page_content = (
            f"<!-- CompiledAt: {now_stamp()} -->\n"
            f"<!-- Source: {key} -->\n"
            f"<!-- SourceHash: {file_hash} -->\n"
            f"<!-- ExtractorVersion: {extractor_ver} -->\n"
            f"<!-- CompilePromptVersion: {COMPILE_PROMPT_VERSION} -->\n\n"
            f"{compiled_body.strip()}\n"
        )
        write_text_file(target, page_content)
        written_pages.append(target)
        manifest[key] = {
            "fingerprint": fingerprint,
            "file_hash": file_hash,
            "extractor_version": extractor_ver,
            "compile_prompt_version": COMPILE_PROMPT_VERSION,
            "target": target.relative_to(config.wiki_dir).as_posix(),
            "updated_at": now_stamp(),
        }
        if progress_cb:
            progress_cb(idx, total, f"Compiled {key}")

    _save_manifest(manifest_file, manifest)
    if progress_cb:
        progress_cb(total, total, "Compile stage finished")
    return written_pages


def _extract_summary_line(markdown_text: str) -> str:
    for line in markdown_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("<!--"):
            continue
        return line[:140]
    return "(no summary)"


def _extract_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            value = line[2:].strip()
            if value:
                return value
    return fallback


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[tuple[int, int, str]]:
    chunks: list[tuple[int, int, str]] = []
    cleaned = text.strip()
    if not cleaned:
        return chunks

    safe_size = max(100, chunk_size)
    safe_overlap = max(0, min(overlap, safe_size - 1))
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + safe_size)
        body = cleaned[start:end].strip()
        if body:
            chunks.append((start, end, body))
        if end >= len(cleaned):
            break
        next_start = max(0, end - safe_overlap)
        if next_start <= start:
            next_start = end
        start = next_start
    return chunks


def build_chunk_index(config: AppConfig) -> list[Path]:
    source_pages = sorted((config.wiki_dir / "sources").glob("*.md"))
    chunks_path = config.wiki_dir / "chunk_index.jsonl"
    meta_path = config.wiki_dir / "chunk_index.meta.json"

    lines: list[str] = []
    total_chunks = 0
    for page in source_pages:
        text = read_text_file(page)
        title = _extract_title(text, page.stem)
        page_chunks = _chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        for idx, (start, end, chunk) in enumerate(page_chunks, start=1):
            row = {
                "chunk_id": f"{page.stem}:{idx}",
                "page_id": page.stem,
                "page_path": f"sources/{page.name}",
                "title": title,
                "text": chunk,
                "char_start": start,
                "char_end": end,
            }
            lines.append(json.dumps(row, ensure_ascii=False))
            total_chunks += 1

    chunk_payload = "\n".join(lines).rstrip() + ("\n" if lines else "")
    write_text_file(chunks_path, chunk_payload)
    write_text_file(
        meta_path,
        json.dumps(
            {
                "updated_at": now_stamp(),
                "chunk_size": CHUNK_SIZE,
                "chunk_overlap": CHUNK_OVERLAP,
                "source_pages": len(source_pages),
                "total_chunks": total_chunks,
                "path": chunks_path.relative_to(config.wiki_dir).as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    return [chunks_path, meta_path]


def build_index(
    config: AppConfig,
    *,
    llm: LLMClient,
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> list[Path]:
    ensure_workspace(config.raw_dir, config.wiki_dir, config.outputs_dir)
    source_pages = sorted((config.wiki_dir / "sources").glob("*.md"))
    total_steps = 3 if source_pages else 1

    if progress_cb:
        progress_cb(0, total_steps, "Building wiki index")

    lines = ["# Wiki Index", "", f"- Updated: {now_stamp()}", ""]
    if not source_pages:
        lines += ["No compiled source pages found under `wiki/sources/`."]
    else:
        lines += ["## Source Pages", ""]
        for page in source_pages:
            text = read_text_file(page)
            summary = _extract_summary_line(text)
            lines.append(f"- [{page.stem}](sources/{page.name}) - {summary}")

    index_path = config.wiki_dir / "index.md"
    write_text_file(index_path, "\n".join(lines).rstrip() + "\n")
    if progress_cb:
        progress_cb(1, total_steps, "Index updated")

    written = [index_path]

    if source_pages:
        chunk_paths = build_chunk_index(config)
        written.extend(chunk_paths)
        if progress_cb:
            progress_cb(2, total_steps, "Chunk index updated")

        summary_blocks: list[str] = []
        max_chars = config.max_context_chars
        consumed = 0
        for page in source_pages:
            text = read_text_file(page)
            snippet = text[:900]
            block = f"## {page.stem}\n{snippet}\n"
            if consumed + len(block) > max_chars:
                break
            summary_blocks.append(block)
            consumed += len(block)

        user_prompt = (
            "Based on these wiki pages, produce a cross-document knowledge map.\n\n"
            + "\n".join(summary_blocks)
        )
        map_text = llm.complete(
            model=config.model,
            system_prompt=KNOWLEDGE_MAP_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=config.temperature_compile,
            max_tokens=config.llm_max_tokens,
        )
        map_path = config.wiki_dir / "knowledge_map.md"
        write_text_file(map_path, map_text.strip() + "\n")
        written.append(map_path)
        if progress_cb:
            progress_cb(3, total_steps, "Knowledge map updated")
    elif progress_cb:
        progress_cb(1, total_steps, "No source pages for chunk index and map")

    return written
