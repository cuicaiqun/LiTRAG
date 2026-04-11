from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".htm",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
}


def ensure_workspace(raw_dir: Path, wiki_dir: Path, outputs_dir: Path) -> None:
    for path in (raw_dir, wiki_dir, outputs_dir, wiki_dir / "sources", wiki_dir / "qa"):
        path.mkdir(parents=True, exist_ok=True)


def iter_text_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files)


def read_text_file(path: Path) -> str:
    encodings = ("utf-8", "utf-8-sig", "gb18030", "latin-1")
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="ignore")


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def now_filename_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def safe_slug(text: str, max_len: int = 80) -> str:
    normalized = text.strip().lower()
    ascii_text = normalized.encode("ascii", errors="ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9\s-]", "", ascii_text)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug:
        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
        slug = f"item-{digest}"
    return slug[:max_len]
