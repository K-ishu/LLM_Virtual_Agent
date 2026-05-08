# Evaluation Plan

## 1. Goal

Evaluate whether the LLM-powered assistant produces useful, structured, and reviewable outputs for software engineering tasks.

## 2. Evaluation Objects

- Requirements generated from project descriptions
- Requirement reviews
- Test cases generated from requirements
- Architecture suggestions
- Effect of optional local dataset context on output structure and usefulness

## 3. Data

The evaluation benchmark is prepared from public online requirements-engineering datasets downloaded once and stored locally:

- PURE requirements documents
- User-story requirements datasets
- FR/NFR requirements dataset
- OWASP security/user-story acceptance criteria

If online data has not been downloaded yet, `prepare_benchmark.py` creates a small seed benchmark from `data/seed_requirements_examples.jsonl` so that the prototype remains demonstrable.

## 4. Metrics

| Metric | Description |
|---|---|
| Correctness | The output is technically plausible and grounded in the input. |
| Completeness | The output covers main functions, constraints, and edge cases. |
| Clarity | The output is understandable, structured, and unambiguous. |
| Consistency | Test cases and architecture elements match the stated requirements. |
| Traceability | Test cases include links to related requirements. |
| Hallucination | The output avoids unsupported facts or labels assumptions. |
| Safety/Privacy | The output identifies relevant security and privacy concerns. |
| Usefulness | A human engineer can directly use or refine the output. |
| Reproducibility | The same benchmark can be regenerated and evaluated from local files. |

## 5. Deterministic Evaluation

The script `evaluation/evaluate_with_rubric.py` checks output structure:

- review summary exists;
- issues exist;
- recommendations exist;
- clarification questions exist;
- test cases exist;
- test cases include steps, expected results, priority, and requirement traceability.

Run without local retrieval:

```bash
python evaluation/evaluate_with_rubric.py --input data/processed/eval_set.json --output data/processed/evaluation_results.json
```

Run with local retrieval:

```bash
python evaluation/evaluate_with_rubric.py --input data/processed/eval_set.json --output data/processed/evaluation_results_with_context.json --use-context
```

## 6. Human Evaluation

A small sample of outputs should be manually scored from 1 to 5 for:

- correctness;
- completeness;
- clarity;
- usefulness;
- safety/privacy awareness;
- degree of hallucination.

Suggested comparison:

1. Run the assistant without local context.
2. Run the assistant with local context.
3. Compare whether context improves coverage, traceability, and security/privacy awareness.

## 7. Acceptance Criteria

The prototype is acceptable if:

- it runs locally through Docker;
- it produces structured outputs for all four main tasks;
- it can process at least 30 benchmark examples after online data download;
- it can run a seed benchmark even without online data;
- generated test cases include traceability for most examples;
- evaluation results are saved and reproducible.
