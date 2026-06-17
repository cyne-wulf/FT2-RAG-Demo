from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

from crunchbase_rag_demo.data import CompanyRecord

TOKEN_RE = re.compile(r"[a-z0-9]+")

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "to",
    "with",
    "which",
    "who",
    "why",
    "company",
    "companies",
    "startup",
    "startups",
    "business",
    "businesses",
    "using",
    "help",
    "helps",
}


@dataclass(frozen=True)
class SearchResult:
    record: CompanyRecord
    score: float


@dataclass
class TfidfIndex:
    records: list[CompanyRecord]
    idf: dict[str, float]
    document_vectors: list[dict[str, float]]
    document_norms: list[float]

    @classmethod
    def build(cls, records: list[CompanyRecord]) -> "TfidfIndex":
        if not records:
            raise ValueError("Cannot build an index with zero records.")

        tokenized_documents = [_tokenize(record.search_text()) for record in records]
        document_count = len(tokenized_documents)
        document_frequencies = Counter(
            token for tokens in tokenized_documents for token in set(tokens)
        )
        idf = {
            token: math.log((1 + document_count) / (1 + frequency)) + 1
            for token, frequency in document_frequencies.items()
        }
        document_vectors = [_weighted_vector(tokens, idf) for tokens in tokenized_documents]
        document_norms = [_norm(vector) for vector in document_vectors]
        return cls(
            records=records,
            idf=idf,
            document_vectors=document_vectors,
            document_norms=document_norms,
        )

    def search(self, query: str, k: int = 5) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("Query must not be empty.")
        query_vector = _weighted_vector(_tokenize(query), self.idf)
        query_norm = _norm(query_vector)
        if query_norm == 0:
            return []

        scored: list[tuple[int, float]] = []
        for index, document_vector in enumerate(self.document_vectors):
            document_norm = self.document_norms[index]
            if document_norm == 0:
                continue
            score = _dot(query_vector, document_vector) / (query_norm * document_norm)
            if score > 0:
                scored.append((index, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [SearchResult(record=self.records[index], score=score) for index, score in scored[:k]]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "records": [asdict(record) for record in self.records],
            "idf": self.idf,
            "document_vectors": self.document_vectors,
            "document_norms": self.document_norms,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "TfidfIndex":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            records=[CompanyRecord(**record) for record in payload["records"]],
            idf={token: float(value) for token, value in payload["idf"].items()},
            document_vectors=[
                {token: float(value) for token, value in vector.items()}
                for vector in payload["document_vectors"]
            ],
            document_norms=[float(value) for value in payload["document_norms"]],
        )


def _tokenize(text: str) -> list[str]:
    words = [token for token in TOKEN_RE.findall(text.lower()) if token not in STOP_WORDS]
    bigrams = [f"{left}_{right}" for left, right in zip(words, words[1:])]
    return words + bigrams


def _weighted_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    counts = Counter(token for token in tokens if token in idf)
    total = sum(counts.values())
    if total == 0:
        return {}
    return {token: (count / total) * idf[token] for token, count in counts.items()}


def _dot(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def _norm(vector: dict[str, float]) -> float:
    return math.sqrt(sum(value * value for value in vector.values()))
