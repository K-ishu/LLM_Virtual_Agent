from app.assistant_core import generate_requirements, generate_test_cases, review_requirements, suggest_architecture
from app.corpus import retrieve_context
from app.llm_client import LLMClient


def test_mock_requirement_generation(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    client = LLMClient()
    result = generate_requirements("Build a web app for managing student study plans.", client=client)
    assert "functional_requirements" in result
    assert len(result["functional_requirements"]) > 0
    assert result["metadata"]["used_local_context"] is False


def test_mock_requirement_generation_with_context(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    client = LLMClient()
    result = generate_requirements("Build a secure student study planner.", client=client, use_context=True)
    assert "functional_requirements" in result
    assert result["metadata"]["used_local_context"] is True


def test_mock_review(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    client = LLMClient()
    result = review_requirements("The system shall be fast and user friendly.", client=client)
    assert "issues" in result
    assert len(result["issues"]) > 0


def test_mock_test_generation(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    client = LLMClient()
    result = generate_test_cases("FR-1: The system shall allow login.", client=client)
    assert "test_cases" in result
    assert len(result["test_cases"]) > 0


def test_mock_architecture(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    client = LLMClient()
    result = suggest_architecture("Build a study planner.", "FR-1: The system shall create plans.", client=client)
    assert "components" in result
    assert len(result["components"]) > 0


def test_retrieve_context_does_not_crash():
    context = retrieve_context("secure student study planner", top_k=1, max_chars=500)
    assert isinstance(context, str)
