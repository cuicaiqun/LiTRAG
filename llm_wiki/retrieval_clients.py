from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from openai import OpenAI


@dataclass(frozen=True)
class EmbeddingClient:
    api_key: str
    base_url: str
    model: str
    dimensions: int = 0

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("EMBEDDING_API_KEY is required.")
        if not self.base_url:
            raise ValueError("EMBEDDING_BASE_URL is required.")
        if not self.model:
            raise ValueError("EMBEDDING_MODEL is required.")
        object.__setattr__(self, "_client", OpenAI(api_key=self.api_key, base_url=self.base_url))

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload: dict[str, Any] = {
            "model": self.model,
            "input": texts,
        }
        if self.dimensions > 0:
            payload["dimensions"] = self.dimensions

        try:
            response = self._client.embeddings.create(**payload)
        except TypeError:
            payload.pop("dimensions", None)
            response = self._client.embeddings.create(**payload)

        vectors: list[list[float]] = []
        for item in response.data:
            embedding = getattr(item, "embedding", None)
            if isinstance(embedding, list) and embedding:
                vectors.append([float(x) for x in embedding])

        if len(vectors) != len(texts):
            raise RuntimeError(
                f"Embedding API returned {len(vectors)} vectors for {len(texts)} inputs."
            )
        return vectors


@dataclass(frozen=True)
class RerankClient:
    api_key: str
    base_url: str
    model: str
    timeout_sec: int = 45

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("RERANK_API_KEY is required.")
        if not self.base_url:
            raise ValueError("RERANK_BASE_URL is required.")
        if not self.model:
            raise ValueError("RERANK_MODEL is required.")

    def rerank(self, *, query: str, documents: list[str], top_n: int | None = None) -> list[float]:
        if not documents:
            return []
        req_top_n = max(1, min(top_n or len(documents), len(documents)))
        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": req_top_n,
            "return_documents": False,
        }
        response = requests.post(
            f"{self.base_url.rstrip('/')}/rerank",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout_sec,
        )
        if response.status_code >= 400:
            snippet = response.text[:240]
            raise RuntimeError(f"Rerank request failed ({response.status_code}): {snippet}")

        body = response.json()
        raw_results = body.get("results")
        if not isinstance(raw_results, list):
            raw_results = body.get("data")
        if not isinstance(raw_results, list):
            raise RuntimeError("Rerank response missing `results` or `data` list.")

        doc_to_index: dict[str, int] = {}
        for i, doc in enumerate(documents):
            if doc not in doc_to_index:
                doc_to_index[doc] = i

        scores = [0.0] * len(documents)
        for idx, item in enumerate(raw_results):
            if not isinstance(item, dict):
                continue
            score_raw = item.get("relevance_score", item.get("score", item.get("relevance", 0.0)))
            try:
                score = float(score_raw)
            except (TypeError, ValueError):
                score = 0.0

            doc_index = item.get("index")
            if isinstance(doc_index, int):
                target_index = doc_index
            else:
                candidate_doc = item.get("document")
                if isinstance(candidate_doc, str):
                    target_index = doc_to_index.get(candidate_doc, idx)
                elif isinstance(candidate_doc, dict):
                    doc_text = candidate_doc.get("text", "")
                    if isinstance(doc_text, str):
                        target_index = doc_to_index.get(doc_text, idx)
                    else:
                        target_index = idx
                else:
                    target_index = idx

            if 0 <= target_index < len(scores):
                scores[target_index] = score
        return scores
