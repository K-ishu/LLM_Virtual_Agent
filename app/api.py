"""Optional FastAPI backend."""

from fastapi import FastAPI

from app.assistant_core import (
    analyze_code,
    generate_attack_scenarios,
    generate_requirements,
    generate_test_cases,
    review_requirements,
    suggest_architecture,
)
from app.corpus import corpus_status
from app.schemas import ArchitectureRequest, AttackScenarioRequest, CodeTextRequest, ProjectDescriptionRequest, RequirementsTextRequest

app = FastAPI(title="LLM Software Engineering Assistant")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/corpus/status")
def get_corpus_status() -> dict:
    return corpus_status()


@app.post("/requirements")
def requirements(payload: ProjectDescriptionRequest) -> dict:
    return generate_requirements(payload.project_description, use_context=payload.use_context)


@app.post("/review")
def review(payload: RequirementsTextRequest) -> dict:
    return review_requirements(payload.requirements_text, use_context=payload.use_context)


@app.post("/test-cases")
def tests(payload: RequirementsTextRequest) -> dict:
    return generate_test_cases(payload.requirements_text, use_context=payload.use_context)


@app.post("/architecture")
def architecture(payload: ArchitectureRequest) -> dict:
    return suggest_architecture(payload.project_description, payload.requirements_text, use_context=payload.use_context)


@app.post("/code-analysis")
def code_analysis(payload: CodeTextRequest) -> dict:
    return analyze_code(payload.code_text, use_context=payload.use_context)


@app.post("/attack-scenarios")
def attack_scenarios(payload: AttackScenarioRequest) -> dict:
    return generate_attack_scenarios(payload.project_description, payload.requirements_text, use_context=payload.use_context)
