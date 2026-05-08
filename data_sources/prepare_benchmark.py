"""Prepare a reproducible local benchmark from downloaded datasets.

The goal is not to train a large model. The goal is to create a fixed local
corpus for RAG-style context retrieval and a small evaluation set for testing
assistant outputs.

Run after downloading data:
    python data_sources/prepare_benchmark.py
"""

from __future__ import annotations

import csv
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SEED_PATH = PROJECT_ROOT / "data" / "seed_requirements_examples.jsonl"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _record(source_file: str, text: str, label: str | None = None) -> dict:
    payload = {"source_file": source_file, "text": _clean_text(text)}
    if label:
        payload["label"] = label
    return payload


def extract_text_from_file_bytes(name: str, raw: bytes) -> str:
    suffix = Path(name).suffix.lower()
    if suffix == ".xml":
        root = ET.fromstring(raw)
        return _clean_text(" ".join(root.itertext()))
    if suffix in {".txt", ".md", ".csv", ".tsv"}:
        return _clean_text(raw.decode("utf-8", errors="ignore"))
    return ""


def extract_text_from_zip(zip_path: Path, limit: int = 200) -> list[dict]:
    examples: list[dict] = []
    if not zip_path.exists():
        return examples
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if len(examples) >= limit:
                break
            if name.endswith("/"):
                continue
            try:
                text = extract_text_from_file_bytes(name, archive.read(name))
            except (KeyError, ET.ParseError, UnicodeDecodeError):
                continue
            if len(text) < 80:
                continue
            examples.append(_record(name, text[:2000]))
    return examples


def extract_plain_text_files(folder: Path, limit: int = 200) -> list[dict]:
    examples: list[dict] = []
    for path in folder.rglob("*"):
        if len(examples) >= limit:
            break
        if not path.is_file() or path.suffix.lower() not in {".txt", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = [_clean_text(line) for line in text.splitlines()]
        # Prefer line-level user stories/requirements when available.
        usable_lines = [line for line in lines if len(line) >= 40 and not line.startswith("#")]
        if usable_lines:
            for line in usable_lines:
                examples.append(_record(str(path.relative_to(PROJECT_ROOT)), line))
                if len(examples) >= limit:
                    break
        elif len(_clean_text(text)) >= 80:
            examples.append(_record(str(path.relative_to(PROJECT_ROOT)), text[:2000]))
    return examples[:limit]


def extract_user_story_examples(folder: Path, limit: int = 200) -> list[dict]:
    examples: list[dict] = []
    for zip_path in folder.glob("*.zip"):
        examples.extend(extract_text_from_zip(zip_path, limit=limit - len(examples)))
        if len(examples) >= limit:
            return examples[:limit]
    examples.extend(extract_plain_text_files(folder, limit=limit - len(examples)))
    return examples[:limit]


def extract_fr_nfr_examples(folder: Path, limit: int = 200) -> list[dict]:
    examples: list[dict] = []

    for path in folder.rglob("*"):
        if len(examples) >= limit:
            break
        if not path.is_file():
            continue
        suffix = path.suffix.lower()

        if suffix in {".csv", ".tsv"}:
            delimiter = "\t" if suffix == ".tsv" else ","
            with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
                sample = handle.read(4096)
                handle.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    delimiter = dialect.delimiter
                except csv.Error:
                    pass
                reader = csv.DictReader(handle, delimiter=delimiter)
                for row in reader:
                    values = {k.lower(): v for k, v in row.items() if k and v}
                    text = values.get("requirement") or values.get("requirements") or values.get("text") or values.get("sentence")
                    label = values.get("class") or values.get("label") or values.get("type") or values.get("category")
                    if text and len(_clean_text(text)) >= 20:
                        examples.append(_record(str(path.relative_to(PROJECT_ROOT)), text, label))
                    if len(examples) >= limit:
                        break

        elif suffix in {".xlsx", ".xls"}:
            try:
                import pandas as pd

                frames = pd.read_excel(path, sheet_name=None)
            except Exception:
                continue
            for _, frame in frames.items():
                lower_cols = {str(col).lower(): col for col in frame.columns}
                text_col = next((lower_cols[c] for c in ["requirement", "requirements", "text", "sentence"] if c in lower_cols), None)
                label_col = next((lower_cols[c] for c in ["class", "label", "type", "category"] if c in lower_cols), None)
                if text_col is None:
                    continue
                for _, row in frame.iterrows():
                    text = str(row.get(text_col, ""))
                    label = str(row.get(label_col, "")) if label_col is not None else None
                    if len(_clean_text(text)) >= 20:
                        examples.append(_record(str(path.relative_to(PROJECT_ROOT)), text, label))
                    if len(examples) >= limit:
                        break
                if len(examples) >= limit:
                    break

        elif suffix in {".txt", ".md"} and not path.name.startswith("README"):
            examples.extend(extract_plain_text_files(path.parent, limit=limit - len(examples)))

    return examples[:limit]


def extract_owasp_examples(folder: Path, limit: int = 120) -> list[dict]:
    examples: list[dict] = []
    for path in folder.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            line = _clean_text(line.strip("| "))
            if len(line) >= 45 and not line.lower().startswith(("user story", "acceptance criteria")):
                examples.append(_record(str(path.relative_to(PROJECT_ROOT)), line, label="security"))
            if len(examples) >= limit:
                break
    return examples[:limit]


def load_seed_examples() -> list[dict]:
    if not SEED_PATH.exists():
        return []
    examples: list[dict] = []
    with SEED_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = item.get("text", "")
            if len(_clean_text(text)) >= 30:
                examples.append(_record(item.get("source_file", "seed"), text, item.get("label")))
    return examples


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    pure_dir = RAW_DIR / "pure_requirements"
    user_stories_dir = RAW_DIR / "user_stories"
    fr_nfr_dir = RAW_DIR / "fr_nfr_dataset"
    owasp_dir = RAW_DIR / "owasp_user_security_stories"

    pure_examples: list[dict] = []
    for zip_file in pure_dir.glob("*.zip"):
        pure_examples.extend(extract_text_from_zip(zip_file, limit=160 - len(pure_examples)))
        if len(pure_examples) >= 160:
            break
    # Some Zenodo downloads may extract plain documents rather than a single zip.
    if len(pure_examples) < 20:
        pure_examples.extend(extract_plain_text_files(pure_dir, limit=160 - len(pure_examples)))

    user_story_examples = extract_user_story_examples(user_stories_dir, limit=160)
    fr_nfr_examples = extract_fr_nfr_examples(fr_nfr_dir, limit=160)
    security_examples = extract_owasp_examples(owasp_dir, limit=120)
    seed_examples = load_seed_examples()

    write_jsonl(PROCESSED_DIR / "pure_requirements_examples.jsonl", pure_examples)
    write_jsonl(PROCESSED_DIR / "user_story_examples.jsonl", user_story_examples)
    write_jsonl(PROCESSED_DIR / "fr_nfr_examples.jsonl", fr_nfr_examples)
    write_jsonl(PROCESSED_DIR / "security_requirements_examples.jsonl", security_examples)
    write_jsonl(PROCESSED_DIR / "seed_requirements_examples.jsonl", seed_examples)

    corpus = pure_examples + user_story_examples + fr_nfr_examples + security_examples
    if not corpus:
        # Keeps the app and evaluation demonstrable even before downloading data.
        corpus = seed_examples

    eval_set = []
    for idx, item in enumerate(corpus[:30], start=1):
        eval_set.append(
            {
                "id": f"EVAL-{idx:03d}",
                "input_text": item["text"][:1200],
                "source_file": item["source_file"],
                "tasks": ["review_requirements", "generate_test_cases"],
                "rubric": {
                    "correctness": "Output should be technically plausible and grounded in the input.",
                    "completeness": "Output should cover main functions, constraints, and visible edge cases.",
                    "clarity": "Output should be structured and unambiguous.",
                    "consistency": "Generated tests should trace back to requirements.",
                    "safety_privacy": "Output should identify security/privacy concerns when relevant.",
                },
            }
        )

    (PROCESSED_DIR / "eval_set.json").write_text(json.dumps(eval_set, indent=2), encoding="utf-8")
    summary = {
        "pure_examples": len(pure_examples),
        "user_story_examples": len(user_story_examples),
        "fr_nfr_examples": len(fr_nfr_examples),
        "security_examples": len(security_examples),
        "seed_examples": len(seed_examples),
        "evaluation_items": len(eval_set),
    }
    (PROCESSED_DIR / "benchmark_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
