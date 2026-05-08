"""Evaluate assistant outputs with a simple reproducible rubric.

This script uses deterministic checks. For stronger evaluation, extend it with
human evaluation or LLM-as-judge, but keep the criteria fixed and versioned.

Run:
    python evaluation/evaluate_with_rubric.py --input data/processed/eval_set.json --output data/processed/evaluation_results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.assistant_core import generate_test_cases, review_requirements


def score_review_output(output: dict[str, Any]) -> dict[str, Any]:
    issues = output.get("issues", [])
    clarification_questions = output.get("clarification_questions", [])
    improved_requirements = output.get("improved_requirements", [])

    scores = {
        "has_summary": int(bool(output.get("summary"))),
        "has_quality_issues": int(isinstance(issues, list) and len(issues) > 0),
        "has_recommendations": int(any("recommendation" in item and item["recommendation"] for item in issues if isinstance(item, dict))),
        "has_clarification_questions": int(isinstance(clarification_questions, list) and len(clarification_questions) > 0),
        "has_improved_requirements": int(isinstance(improved_requirements, list) and len(improved_requirements) > 0),
    }
    scores["total"] = sum(scores.values())
    scores["max"] = 5
    return scores


def score_test_output(output: dict[str, Any]) -> dict[str, Any]:
    test_cases = output.get("test_cases", [])
    has_traceability = False
    has_steps = False
    has_expected = False
    has_priority = False
    if isinstance(test_cases, list):
        for item in test_cases:
            if not isinstance(item, dict):
                continue
            has_traceability = has_traceability or bool(item.get("related_requirement_ids"))
            has_steps = has_steps or bool(item.get("steps"))
            has_expected = has_expected or bool(item.get("expected_result"))
            has_priority = has_priority or bool(item.get("priority"))

    scores = {
        "has_test_cases": int(isinstance(test_cases, list) and len(test_cases) > 0),
        "has_traceability": int(has_traceability),
        "has_steps": int(has_steps),
        "has_expected_results": int(has_expected),
        "has_priority": int(has_priority),
    }
    scores["total"] = sum(scores.values())
    scores["max"] = 5
    return scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to eval_set.json")
    parser.add_argument("--output", required=True, help="Path to write results JSON")
    parser.add_argument("--use-context", action="store_true", help="Use the processed local corpus as retrieval context during evaluation")
    args = parser.parse_args()

    input_path = PROJECT_ROOT / args.input if not Path(args.input).is_absolute() else Path(args.input)
    output_path = PROJECT_ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)

    eval_items = json.loads(input_path.read_text(encoding="utf-8"))
    results = []
    for item in eval_items:
        text = item["input_text"]
        review = review_requirements(text, use_context=args.use_context)
        tests = generate_test_cases(text, use_context=args.use_context)
        review_score = score_review_output(review)
        test_score = score_test_output(tests)
        results.append(
            {
                "id": item["id"],
                "source_file": item.get("source_file"),
                "review_score": review_score,
                "test_generation_score": test_score,
                "review_output": review,
                "test_output": tests,
            }
        )

    totals = {
        "items": len(results),
        "used_local_context": args.use_context,
        "average_review_score": sum(r["review_score"]["total"] for r in results) / max(len(results), 1),
        "average_test_generation_score": sum(r["test_generation_score"]["total"] for r in results) / max(len(results), 1),
    }

    payload = {"summary": totals, "results": results}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(totals, indent=2))


if __name__ == "__main__":
    main()
