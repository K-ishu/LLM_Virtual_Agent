"""Local corpus loading and lightweight retrieval for RAG-style context.

The project intentionally downloads public online datasets once, stores them
locally, and retrieves from the local processed corpus during runtime. This
keeps evaluation reproducible and avoids live web dependencies during demos.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


@dataclass(frozen=True)
class CorpusDocument:
    doc_id: str
    source_file: str
    text: str


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _iter_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


@lru_cache(maxsize=1)
def load_local_corpus() -> list[CorpusDocument]:
    """Load processed benchmark/corpus files from data/processed.

    The function is cached because Streamlit reruns the script frequently.
    """
    documents: list[CorpusDocument] = []
    for file_name in [
        "pure_requirements_examples.jsonl",
        "user_story_examples.jsonl",
        "fr_nfr_examples.jsonl",
        "security_requirements_examples.jsonl",
        "seed_requirements_examples.jsonl",
    ]:
        path = PROCESSED_DIR / file_name
        for idx, record in enumerate(_iter_jsonl(path), start=1):
            text = _clean_text(str(record.get("text", "")))
            if len(text) < 30:
                continue
            source_file = str(record.get("source_file", file_name))
            documents.append(
                CorpusDocument(
                    doc_id=f"{file_name}:{idx}",
                    source_file=source_file,
                    text=text[:3000],
                )
            )
    return documents


def retrieve_context(query: str, top_k: int = 3, max_chars: int = 4000) -> str:
    """Return a compact context block from the local corpus.

    Uses TF-IDF cosine similarity when scikit-learn is installed. Falls back to
    token-overlap scoring to keep the project robust in minimal environments.
    """
    documents = load_local_corpus()
    if not documents:
        return ""

    query = _clean_text(query)
    texts = [doc.text for doc in documents]

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(stop_words="english", max_features=8000)
        matrix = vectorizer.fit_transform(texts + [query])
        similarities = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
        ranked_indices = similarities.argsort()[::-1][:top_k]
        ranked = [(int(i), float(similarities[i])) for i in ranked_indices if similarities[i] > 0]
    except Exception:
        query_terms = set(re.findall(r"[A-Za-z0-9_]+", query.lower()))
        scored: list[tuple[int, float]] = []
        for i, text in enumerate(texts):
            terms = set(re.findall(r"[A-Za-z0-9_]+", text.lower()))
            score = len(query_terms & terms) / max(len(query_terms), 1)
            if score > 0:
                scored.append((i, score))
        ranked = sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]

    blocks: list[str] = []
    used_chars = 0
    for idx, score in ranked:
        doc = documents[idx]
        block = f"[source={doc.source_file}; score={score:.3f}]\n{doc.text}"
        if used_chars + len(block) > max_chars:
            block = block[: max(0, max_chars - used_chars)]
        if block:
            blocks.append(block)
            used_chars += len(block)
        if used_chars >= max_chars:
            break

    return "\n\n---\n\n".join(blocks)


def corpus_status() -> dict[str, int | bool]:
    documents = load_local_corpus()
    return {
        "available": bool(documents),
        "documents": len(documents),
    }
