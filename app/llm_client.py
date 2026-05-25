"""LLM client abstraction with mock and OpenAI-compatible providers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str


class LLMClient:
    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None

    def chat(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if self.provider == "mock":
            return LLMResponse(
                text=self._mock_response(user_prompt),
                provider="mock",
                model="deterministic-mock",
            )
        if self.provider == "openai":
            return self._openai_chat(system_prompt, user_prompt)
        raise ValueError(f"Unsupported LLM_PROVIDER: {self.provider}")

    def _openai_chat(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        client = OpenAI(**client_kwargs)
        completion = client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = completion.choices[0].message.content or "{}"
        return LLMResponse(text=content, provider="openai-compatible", model=self.model)

    def _mock_response(self, user_prompt: str) -> str:
        lower = user_prompt.lower()
        if "generate software requirements" in lower:
            data = {
                "assumptions": ["The prototype is intended for academic demonstration."],
                "clarification_questions": ["Who are the primary users?", "What data must be stored?"],
                "functional_requirements": [
                    {"id": "FR-1", "requirement": "The system shall allow the user to submit a project description.", "rationale": "The assistant needs an input artifact."},
                    {"id": "FR-2", "requirement": "The system shall generate functional and non-functional requirements from the submitted description.", "rationale": "This is the core assistant capability."},
                    {"id": "FR-3", "requirement": "The system shall allow the user to review and refine generated outputs.", "rationale": "The project requires human-machine cooperation."},
                ],
                "non_functional_requirements": [
                    {"id": "NFR-1", "quality_attribute": "privacy", "requirement": "The system shall not log sensitive user input unless explicit consent is provided.", "rationale": "Inputs may contain confidential project details."},
                    {"id": "NFR-2", "quality_attribute": "usability", "requirement": "The system shall present outputs in a structured and readable format.", "rationale": "Users need to inspect and approve the assistant's suggestions."},
                ],
                "risks": ["Generated requirements may be incomplete or hallucinated without human validation."],
            }
            return json.dumps(data, indent=2)
        if "review the requirements" in lower:
            data = {
                "summary": "The requirements are reviewable but need measurable acceptance criteria.",
                "issues": [
                    {"id": "ISSUE-1", "severity": "medium", "type": "unverifiable", "evidence": "Words such as fast or user-friendly are not measurable.", "recommendation": "Replace vague adjectives with thresholds or observable criteria."},
                    {"id": "ISSUE-2", "severity": "medium", "type": "privacy", "evidence": "No data-retention rule is stated.", "recommendation": "Add retention and consent requirements."},
                ],
                "improved_requirements": ["The system shall respond to 95% of requests within 5 seconds under normal load."],
                "clarification_questions": ["What performance threshold is acceptable for the prototype?"],
            }
            return json.dumps(data, indent=2)
        if "generate test cases" in lower:
            data = {
                "test_cases": [
                    {
                        "id": "TC-1",
                        "related_requirement_ids": ["FR-1"],
                        "title": "Submit valid project description",
                        "preconditions": ["The application is running."],
                        "steps": ["Open the assistant UI.", "Enter a project description.", "Click Generate Requirements."],
                        "expected_result": "The system returns structured requirements.",
                        "priority": "high",
                        "test_type": "functional",
                    },
                    {
                        "id": "TC-2",
                        "related_requirement_ids": ["NFR-1"],
                        "title": "Avoid storing sensitive input in logs",
                        "preconditions": ["Logging is enabled."],
                        "steps": ["Submit input containing a fake secret token.", "Inspect local logs."],
                        "expected_result": "The secret token is not present in logs.",
                        "priority": "high",
                        "test_type": "privacy",
                    },
                ],
                "coverage_notes": ["Functional and privacy test examples are included."],
                "missing_information": ["Detailed deployment configuration is not specified."],
            }
            return json.dumps(data, indent=2)
        if "propose a simple architecture" in lower:
            data = {
                "architecture_style": "Layered web application with an LLM service boundary",
                "components": [
                    {"name": "User Interface", "responsibility": "Collect inputs and display structured outputs.", "inputs": ["Project description"], "outputs": ["User commands"]},
                    {"name": "Assistant Backend", "responsibility": "Apply prompts, call the LLM, validate JSON outputs.", "inputs": ["User command"], "outputs": ["Structured JSON"]},
                    {"name": "Evaluation Module", "responsibility": "Score output quality and record reproducible results.", "inputs": ["Generated outputs"], "outputs": ["Evaluation report"]},
                ],
                "data_flow": ["User submits text to UI", "Backend creates task-specific prompt", "LLM returns JSON", "Backend validates and displays result"],
                "technology_stack": ["Python", "Streamlit", "FastAPI", "OpenAI-compatible LLM", "Docker"],
                "deployment_view": "Local Docker deployment with one Streamlit service; FastAPI can be run separately if needed.",
                "security_privacy_considerations": ["Do not store sensitive input by default.", "Keep API keys in environment variables."],
                "human_in_the_loop_points": ["User approves requirements", "User refines ambiguous requirements", "User validates generated test cases"],
            }
            return json.dumps(data, indent=2)

        if "analyze a code snippet" in lower:
            data = {
                "summary": "The snippet can be reviewed for behavior, maintainability, and defensive security concerns.",
                "assumptions": ["The code snippet is incomplete and reviewed statically."],
                "detected_language": "unknown or inferred from snippet",
                "quality_findings": [
                    {"id": "QF-1", "severity": "medium", "category": "reliability", "evidence": "Input validation and error handling are not visible in the snippet.", "recommendation": "Validate inputs, handle expected exceptions, and add tests for invalid input."},
                    {"id": "QF-2", "severity": "medium", "category": "security", "evidence": "No authentication, authorization, or secret-handling context is visible.", "recommendation": "Ensure secrets are stored in environment variables and access checks are explicit."},
                ],
                "refactoring_suggestions": ["Separate input validation, business logic, and persistence code where applicable."],
                "safe_test_ideas": ["Test valid input, invalid input, boundary cases, and authorization failures."],
            }
            return json.dumps(data, indent=2)
        if "generate defensive attack" in lower:
            data = {
                "threat_model_assumptions": ["The system is a web application that stores user data and exposes authenticated workflows."],
                "attack_scenarios": [
                    {
                        "id": "AS-1",
                        "title": "Unauthorized access to another user's records",
                        "asset_at_risk": "User personal data",
                        "threat_actor": "Authenticated malicious user",
                        "scenario": "A user attempts to access or modify resources belonging to another user because object-level authorization is missing.",
                        "impact": "high",
                        "likelihood": "medium",
                        "mitigations": ["Enforce object-level authorization on every request.", "Use server-side ownership checks."],
                        "validation_tests": ["Verify that user A cannot read, update, or delete user B resources."],
                    },
                    {
                        "id": "AS-2",
                        "title": "Abuse of weak authentication policy",
                        "asset_at_risk": "Accounts and session integrity",
                        "threat_actor": "External attacker",
                        "scenario": "Repeated login attempts or weak password policies increase the risk of account compromise.",
                        "impact": "medium",
                        "likelihood": "medium",
                        "mitigations": ["Add rate limiting.", "Require strong passwords or multi-factor authentication where appropriate."],
                        "validation_tests": ["Verify lockout or throttling behavior after repeated failed login attempts."],
                    },
                ],
                "unsafe_scenarios": [
                    {
                        "id": "US-1",
                        "title": "Unsafe or misleading recommendation",
                        "scenario": "The assistant suggests an action without enough context or without warning that human validation is required.",
                        "affected_users": ["End users", "Engineers"],
                        "harm": "Incorrect decisions, privacy exposure, or system misuse.",
                        "mitigations": ["Display assumptions and confidence limits.", "Require human approval for high-impact outputs."],
                        "validation_tests": ["Submit incomplete requirements and verify the assistant asks clarification questions instead of inventing facts."],
                    }
                ],
                "residual_risks": ["Some risks require domain expert review and cannot be fully eliminated by prompt engineering."],
            }
            return json.dumps(data, indent=2)
        return json.dumps({"message": "Mock response: unsupported task."}, indent=2)
