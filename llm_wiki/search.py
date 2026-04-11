from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import requests

from .io_utils import now_filename_stamp, safe_slug, write_text_file


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    content: str
    score: float


@dataclass(frozen=True)
class SearchResult:
    answer: str
    hits: list[SearchHit]


class TavilyClient:
    def __init__(self, *, api_key: str, base_url: str = "https://api.tavily.com") -> None:
        if not api_key:
            raise ValueError("TAVILY_API_KEY is required for web search.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def search(self, *, query: str, max_results: int = 5, search_depth: str = "advanced") -> SearchResult:
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": True,
            "include_raw_content": False,
        }
        response = requests.post(
            f"{self.base_url}/search",
            json=payload,
            timeout=45,
        )
        if response.status_code >= 400:
            snippet = response.text[:240]
            raise RuntimeError(f"Tavily request failed ({response.status_code}): {snippet}")

        data = response.json()
        answer = data.get("answer", "") or ""
        raw_hits = data.get("results", []) or []
        hits: list[SearchHit] = []
        for item in raw_hits:
            hits.append(
                SearchHit(
                    title=str(item.get("title", "")).strip(),
                    url=str(item.get("url", "")).strip(),
                    content=str(item.get("content", "")).strip(),
                    score=float(item.get("score") or 0.0),
                )
            )
        return SearchResult(answer=answer, hits=hits)


def save_search_to_raw(raw_dir: Path, *, query: str, result: SearchResult) -> Path:
    ts = now_filename_stamp()
    slug = safe_slug(query, max_len=60)
    target = raw_dir / "web" / f"{ts}-{slug}.md"

    lines: list[str] = [
        "# Web Search Capture",
        "",
        f"- query: {query}",
        f"- captured_at: {ts}",
        "- provider: tavily",
        "",
    ]

    if result.answer:
        lines.extend(["## Tavily Answer", result.answer.strip(), ""])

    lines.append("## Results")
    if not result.hits:
        lines.append("- (no result)")
    else:
        for idx, hit in enumerate(result.hits, start=1):
            lines.extend(
                [
                    f"### {idx}. {hit.title or '(untitled)'}",
                    f"- url: {hit.url}",
                    f"- score: {hit.score:.4f}",
                    "",
                    hit.content or "(empty snippet)",
                    "",
                ]
            )

    write_text_file(target, "\n".join(lines).rstrip() + "\n")
    return target

