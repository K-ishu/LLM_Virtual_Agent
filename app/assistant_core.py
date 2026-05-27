"""Core assistant functions."""

from __future__ import annotations
import ast
import json
import re
from typing import Any

from app.corpus import retrieve_context
from app.llm_client import LLMClient
from app.prompts import (
    ARCHITECTURE_PROMPT,
    ATTACK_SCENARIO_PROMPT,
    CODE_ANALYSIS_PROMPT,
    REQUIREMENTS_PROMPT,
    REVIEW_PROMPT,
    SYSTEM_PROMPT,
    TEST_CASE_PROMPT,
)

NO_CONTEXT = "No local corpus context provided."


def _extract_json(text: str) -> dict[str, Any]:
    """Parse JSON robustly, with fallbacks for fenced or slightly malformed model outputs."""
    cleaned = (text or "").strip()

    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = cleaned.replace("```", "").strip()

    candidates: list[str] = [cleaned]

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        candidate = candidate.strip()

        candidate = (
            candidate.replace("“", '"')
            .replace("”", '"')
            .replace("’", "'")
            .replace("‘", "'")
        )

        candidate = re.sub(r",(\s*[}\]])", r"\1", candidate)

        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        try:
            data = ast.literal_eval(candidate)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    raise json.JSONDecodeError("Could not parse model output as JSON", cleaned, 0)
def _fallback_attack_payload(project_description: str, requirements_text: str) -> dict[str, Any]:
    """Safe fallback if the model returns invalid JSON for security scenarios."""
    return {
        "threat_model_assumptions": [
            "The system is internet-accessible.",
            "The system stores user and operational data.",
            "Authentication and authorization are required for protected actions.",
        ],
        "attack_scenarios": [
            {
                "id": "AS-1",
                "title": "Unauthorized access to records",
                "asset_at_risk": "Patient, doctor, and appointment records",
                "threat_actor": "Malicious user or external attacker",
                "scenario": "An attacker attempts to access or modify records belonging to another user.",
                "impact": "high",
                "likelihood": "medium",
                "mitigations": [
                    "Enforce role-based access control.",
                    "Check object ownership on every request.",
                    "Enable audit logging for sensitive actions.",
                ],
                "validation_tests": [
                    "Verify that one patient cannot access another patient's appointment details.",
                    "Verify that only admins can manage clinic policies.",
                ],
            }
        ],
        "unsafe_scenarios": [
            {
                "id": "US-1",
                "title": "Sensitive data exposure",
                "scenario": "Personal or health-related data is displayed to unauthorized users or leaked through logs.",
                "affected_users": ["Patients", "Doctors", "Administrators"],
                "harm": "Privacy breach, trust loss, and possible legal or compliance impact.",
                "mitigations": [
                    "Mask sensitive fields in logs.",
                    "Encrypt data at rest and in transit.",
                    "Limit data exposure in UI responses.",
                ],
                "validation_tests": [
                    "Inspect logs for sensitive data leakage.",
                    "Verify TLS is enforced for all user traffic.",
                ],
            }
        ],
        "residual_risks": [
            "Advanced attacks still require deeper security review and penetration testing."
        ],
    }
def _context_for(query: str, use_context: bool) -> str:
    if not use_context:
        return NO_CONTEXT
    context = retrieve_context(query)
    return context or "Local corpus requested, but no processed corpus was found. Run data_sources/download_datasets.py and data_sources/prepare_benchmark.py."


def _attach_metadata(data: dict[str, Any], response_provider: str, response_model: str, task: str, use_context: bool) -> dict[str, Any]:
    data["metadata"] = {
        "provider": response_provider,
        "model": response_model,
        "task": task,
        "used_local_context": use_context,
    }
    return data


def generate_requirements(project_description: str, client: LLMClient | None = None, use_context: bool = False) -> dict[str, Any]:
    client = client or LLMClient()
    prompt = REQUIREMENTS_PROMPT.format(
        project_description=project_description,
        reference_context=_context_for(project_description, use_context),
    )
    response = client.chat(SYSTEM_PROMPT, prompt)
    data = _extract_json(response.text)
    return _attach_metadata(data, response.provider, response.model, "generate_requirements", use_context)


def review_requirements(requirements_text: str, client: LLMClient | None = None, use_context: bool = False) -> dict[str, Any]:
    client = client or LLMClient()
    prompt = REVIEW_PROMPT.format(
        requirements_text=requirements_text,
        reference_context=_context_for(requirements_text, use_context),
    )
    response = client.chat(SYSTEM_PROMPT, prompt)
    data = _extract_json(response.text)
    return _attach_metadata(data, response.provider, response.model, "review_requirements", use_context)


def generate_test_cases(requirements_text: str, client: LLMClient | None = None, use_context: bool = False) -> dict[str, Any]:
    client = client or LLMClient()
    prompt = TEST_CASE_PROMPT.format(
        requirements_text=requirements_text,
        reference_context=_context_for(requirements_text, use_context),
    )
    response = client.chat(SYSTEM_PROMPT, prompt)
    data = _extract_json(response.text)
    return _attach_metadata(data, response.provider, response.model, "generate_test_cases", use_context)


def suggest_architecture(
    project_description: str,
    requirements_text: str,
    client: LLMClient | None = None,
    use_context: bool = False,
) -> dict[str, Any]:
    client = client or LLMClient()
    combined_query = f"{project_description}\n\n{requirements_text}"
    prompt = ARCHITECTURE_PROMPT.format(
        project_description=project_description,
        requirements_text=requirements_text,
        reference_context=_context_for(combined_query, use_context),
    )
    response = client.chat(SYSTEM_PROMPT, prompt)
    data = _extract_json(response.text)
    return _attach_metadata(data, response.provider, response.model, "suggest_architecture", use_context)



def analyze_code(code_text: str, client: LLMClient | None = None, use_context: bool = False) -> dict[str, Any]:
    """Analyze a code snippet for behavior, quality, bugs, and basic security issues."""
    client = client or LLMClient()
    prompt = CODE_ANALYSIS_PROMPT.format(
        code_text=code_text,
        reference_context=_context_for(code_text, use_context),
    )
    response = client.chat(SYSTEM_PROMPT, prompt)
    data = _extract_json(response.text)
    return _attach_metadata(data, response.provider, response.model, "analyze_code", use_context)


def generate_attack_scenarios(
    project_description: str,
    requirements_text: str,
    client: LLMClient | None = None,
    use_context: bool = False,
) -> dict[str, Any]:
    """Generate defensive attack, misuse, and unsafe scenarios with mitigations."""
    if _is_generic_or_too_short(project_description):
        return _insufficient_project_payload("generate_attack_scenarios")

    client = client or LLMClient()
    combined_query = f"{project_description}\n\n{requirements_text}"
    prompt = ATTACK_SCENARIO_PROMPT.format(
        project_description=project_description,
        requirements_text=requirements_text,
        reference_context=_context_for(combined_query, use_context),
    )
    response = client.chat(SYSTEM_PROMPT, prompt)

    try:
        data = _extract_json(response.text)
    except Exception:
        data = _fallback_attack_payload(project_description, requirements_text)

    return _attach_metadata(data, response.provider, response.model, "generate_attack_scenarios", use_context)