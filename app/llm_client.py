"""LLM client abstraction with mock and OpenAI-compatible providers.

The mock provider is deterministic and designed for reproducible demos, tests,
CI/CD, Docker, Render, and Kubernetes deployments. It is not a real LLM, but it
now performs basic input validation and returns domain-aware structured outputs
instead of blindly generating artifacts for invalid inputs such as "hi".
"""

from __future__ import annotations

import json
import os
import re
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

    # ---------------------------------------------------------------------
    # Deterministic mock provider helpers
    # ---------------------------------------------------------------------

    def _extract_user_artifact(self, user_prompt: str) -> str:
        """Extract the actual user-provided project/code text from a prompt.

        The application builds task-specific prompts around the user input. This
        helper tries common prompt markers first and then removes known task
        instructions so that validation is based on the user's artifact, not the
        whole prompt template.
        """
        markers = [
            "Project description:",
            "project description:",
            "Software project description:",
            "software project description:",
            "Requirements:",
            "requirements:",
            "Code snippet:",
            "code snippet:",
            "Input:",
            "input:",
            "User input:",
            "user input:",
        ]

        for marker in markers:
            if marker in user_prompt:
                text = user_prompt.split(marker, 1)[1]
                return self._clean_extracted_text(text)

        # Fallback: remove common instruction fragments and keep remaining text.
        text = re.sub(
            r"(?i)generate software requirements|review the requirements|generate test cases|"
            r"propose a simple architecture|analyze a code snippet|generate defensive attack.*?scenarios",
            " ",
            user_prompt,
        )
        return self._clean_extracted_text(text)

    @staticmethod
    def _clean_extracted_text(text: str) -> str:
        # Stop at common prompt sections that usually follow the user artifact.
        stop_markers = [
            "Return JSON",
            "Return valid JSON",
            "Expected output",
            "Output schema",
            "Use the following",
            "Local context",
            "Context:",
        ]
        for marker in stop_markers:
            if marker in text:
                text = text.split(marker, 1)[0]

        return text.strip().strip("` \n\t:")

    @staticmethod
    def _is_insufficient_input(text: str, *, code_task: bool = False) -> bool:
        normalized = text.strip().lower()
        words = [w for w in re.split(r"\s+", normalized) if w]
        generic_inputs = {
            "hi",
            "hello",
            "test",
            "ok",
            "yes",
            "no",
            "ciao",
            "salam",
            "سلام",
            "hey",
        }

        if not normalized or normalized in generic_inputs:
            return True

        # Code snippets can be short but still valid, e.g. "x = 1". For code
        # analysis, require either code-like symbols or a minimum amount of text.
        if code_task:
            code_like = any(token in text for token in ["def ", "class ", "=", "{", "}", "(", ")", ";"])
            return not code_like and len(words) < 8

        return len(words) < 8

    @staticmethod
    def _insufficient_input_response(task: str) -> str:
        data = {
            "status": "insufficient_input",
            "task": task,
            "message": "The input is too short or too generic to generate meaningful software-engineering artifacts.",
            "required_input": [
                "Describe the goal of the software system.",
                "Identify the primary users or stakeholders.",
                "List the main features or workflows.",
                "Mention important data, constraints, privacy, or security concerns.",
            ],
            "example_input": (
                "Build a web application that helps students plan study schedules. "
                "Users can enter courses, deadlines, available study hours, and preferred study times. "
                "The system suggests a weekly study plan and lets the student revise it."
            ),
            "clarification_questions": [
                "What problem should the software solve?",
                "Who are the primary users?",
                "What are the main features?",
                "What data must be stored or protected?",
            ],
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def _domain_from_text(text: str) -> str:
        lower = text.lower()
        if any(k in lower for k in ["student", "study", "course", "deadline", "schedule"]):
            return "study_planner"
        if any(k in lower for k in ["clinic", "doctor", "patient", "appointment", "medical"]):
            return "clinic_booking"
        if any(k in lower for k in ["bank", "fraud", "transaction", "loan", "payment"]):
            return "finance"
        return "generic_web_app"

    def _mock_response(self, user_prompt: str) -> str:
        lower = user_prompt.lower()
        artifact = self._extract_user_artifact(user_prompt)

        if "generate software requirements" in lower:
            if self._is_insufficient_input(artifact):
                return self._insufficient_input_response("requirements_generation")
            return self._mock_requirements(artifact)

        if "review the requirements" in lower:
            if self._is_insufficient_input(artifact):
                return self._insufficient_input_response("requirements_review")
            return self._mock_review(artifact)

        if "generate test cases" in lower:
            if self._is_insufficient_input(artifact):
                return self._insufficient_input_response("test_case_generation")
            return self._mock_test_cases(artifact)

        if "propose a simple architecture" in lower:
            if self._is_insufficient_input(artifact):
                return self._insufficient_input_response("architecture_suggestion")
            return self._mock_architecture(artifact)

        if "analyze a code snippet" in lower:
            if self._is_insufficient_input(artifact, code_task=True):
                return self._insufficient_input_response("code_analysis")
            return self._mock_code_analysis(artifact)

        if "generate defensive attack" in lower:
            if self._is_insufficient_input(artifact):
                return self._insufficient_input_response("attack_and_unsafe_scenario_generation")
            return self._mock_attack_scenarios(artifact)

        return json.dumps({"message": "Mock response: unsupported task."}, indent=2)

    def _mock_requirements(self, text: str) -> str:
        domain = self._domain_from_text(text)

        if domain == "study_planner":
            functional = [
                ("FR-1", "The system shall allow students to enter courses, deadlines, available study hours, and preferred study times."),
                ("FR-2", "The system shall generate a weekly study plan based on deadlines, available hours, and user preferences."),
                ("FR-3", "The system shall allow students to manually revise the generated study plan."),
            ]
            non_functional = [
                ("NFR-1", "privacy", "The system shall protect students' schedule data and avoid exposing personal availability to unauthorized users."),
                ("NFR-2", "usability", "The system shall present the weekly plan in a clear and editable format."),
            ]
        elif domain == "clinic_booking":
            functional = [
                ("FR-1", "The system shall allow patients to register, log in, and manage their profile."),
                ("FR-2", "The system shall allow patients to book, cancel, and reschedule medical appointments."),
                ("FR-3", "The system shall allow doctors to manage their availability."),
            ]
            non_functional = [
                ("NFR-1", "privacy", "The system shall protect patient and appointment data according to privacy-by-design principles."),
                ("NFR-2", "reliability", "The system shall prevent double booking of the same doctor and time slot."),
            ]
        elif domain == "finance":
            functional = [
                ("FR-1", "The system shall ingest transaction records for fraud-monitoring analysis."),
                ("FR-2", "The system shall flag suspicious transactions for human review."),
                ("FR-3", "The system shall display fraud-risk indicators in a dashboard."),
            ]
            non_functional = [
                ("NFR-1", "security", "The system shall protect financial records using authentication and access control."),
                ("NFR-2", "auditability", "The system shall keep an audit trail of alerts and reviewer decisions."),
            ]
        else:
            functional = [
                ("FR-1", "The system shall allow users to submit and manage domain-specific records."),
                ("FR-2", "The system shall process user input and return structured outputs."),
                ("FR-3", "The system shall allow users to review, refine, and confirm generated outputs."),
            ]
            non_functional = [
                ("NFR-1", "privacy", "The system shall avoid storing sensitive input unless explicitly required."),
                ("NFR-2", "usability", "The system shall present outputs in a structured and readable format."),
            ]

        data = {
            "assumptions": ["The description is an initial project idea and requires stakeholder validation."],
            "clarification_questions": [
                "Who are the primary users and administrators?",
                "What data must be stored, retained, or deleted?",
                "Are there security, privacy, or compliance constraints?",
            ],
            "functional_requirements": [
                {"id": rid, "requirement": req, "rationale": "Derived from the submitted project description."}
                for rid, req in functional
            ],
            "non_functional_requirements": [
                {"id": rid, "quality_attribute": qa, "requirement": req, "rationale": "Needed for deployable and trustworthy operation."}
                for rid, qa, req in non_functional
            ],
            "risks": ["Generated requirements must be validated by a human engineer before implementation."],
        }
        return json.dumps(data, indent=2)

    def _mock_review(self, text: str) -> str:
        data = {
            "summary": "The submitted description is understandable but needs more measurable constraints and acceptance criteria.",
            "issues": [
                {
                    "id": "ISSUE-1",
                    "severity": "medium",
                    "type": "ambiguity",
                    "evidence": "Some features are described at a high level without operational details.",
                    "recommendation": "Define exact user roles, inputs, outputs, and acceptance criteria for each workflow.",
                },
                {
                    "id": "ISSUE-2",
                    "severity": "medium",
                    "type": "privacy/security",
                    "evidence": "The description does not specify authentication, authorization, or data-retention rules.",
                    "recommendation": "Add requirements for access control, data minimization, and secure storage.",
                },
            ],
            "improved_requirements": [
                "The system shall authenticate users before allowing access to personal records.",
                "The system shall define measurable response-time and availability targets for the prototype.",
            ],
            "clarification_questions": [
                "Which user roles are allowed to create, edit, or delete records?",
                "What is the expected maximum number of users or requests during the demo?",
            ],
        }
        return json.dumps(data, indent=2)

    def _mock_test_cases(self, text: str) -> str:
        domain = self._domain_from_text(text)
        if domain == "study_planner":
            main_title = "Generate weekly study plan from valid course and deadline data"
            expected = "The system returns a weekly plan that respects available hours and upcoming deadlines."
        elif domain == "clinic_booking":
            main_title = "Book an available medical appointment"
            expected = "The system confirms the appointment and prevents double booking."
        else:
            main_title = "Submit valid project workflow data"
            expected = "The system processes the input and returns a structured result."

        data = {
            "test_cases": [
                {
                    "id": "TC-1",
                    "related_requirement_ids": ["FR-1", "FR-2"],
                    "title": main_title,
                    "preconditions": ["The application is running.", "The user has valid input data."],
                    "steps": ["Open the UI.", "Enter the required data.", "Submit the request."],
                    "expected_result": expected,
                    "priority": "high",
                    "test_type": "functional",
                },
                {
                    "id": "TC-2",
                    "related_requirement_ids": ["NFR-1"],
                    "title": "Reject insufficient or invalid input",
                    "preconditions": ["The application is running."],
                    "steps": ["Submit a very short input such as 'hi'.", "Trigger generation."],
                    "expected_result": "The system asks clarification questions instead of inventing detailed artifacts.",
                    "priority": "high",
                    "test_type": "robustness",
                },
            ],
            "coverage_notes": ["Functional and robustness tests are included."],
            "missing_information": ["More domain-specific acceptance criteria should be added after stakeholder validation."],
        }
        return json.dumps(data, indent=2)

    def _mock_architecture(self, text: str) -> str:
        domain = self._domain_from_text(text)
        components = [
            {"name": "Streamlit User Interface", "responsibility": "Collect project input and display structured assistant outputs.", "inputs": ["User text", "Selected task"], "outputs": ["Task request"]},
            {"name": "Assistant Core", "responsibility": "Route the request to the selected software-engineering workflow.", "inputs": ["Task request"], "outputs": ["Task-specific prompt"]},
            {"name": "LLM Provider Boundary", "responsibility": "Generate or mock structured JSON responses.", "inputs": ["Prompt"], "outputs": ["JSON artifact"]},
            {"name": "Evaluation Module", "responsibility": "Score generated outputs using a rubric-based evaluation pipeline.", "inputs": ["Generated artifacts"], "outputs": ["Evaluation report"]},
        ]
        if domain in {"study_planner", "clinic_booking", "finance"}:
            components.append({"name": "Domain Data Store", "responsibility": "Persist user/domain records if the prototype is extended beyond mock mode.", "inputs": ["Validated records"], "outputs": ["Stored history"]})

        data = {
            "architecture_style": "Layered web application with a replaceable LLM provider boundary",
            "components": components,
            "data_flow": [
                "User enters a project description or code snippet.",
                "The UI sends the selected task and input to the assistant core.",
                "The assistant core builds a task-specific prompt.",
                "The LLM provider returns structured JSON.",
                "The UI renders the result for human review.",
            ],
            "technology_stack": ["Python", "Streamlit", "OpenAI-compatible provider", "Pytest", "Docker", "GitHub Actions", "Render", "Kubernetes"],
            "deployment_view": "The same application can run locally, in Docker, on Render, and through Kubernetes port-forwarding.",
            "security_privacy_considerations": [
                "Keep API keys in environment variables.",
                "Reject insufficient input instead of inventing unsupported details.",
                "Use human validation before accepting generated engineering artifacts.",
            ],
            "human_in_the_loop_points": ["User validates requirements", "User refines ambiguous outputs", "User approves test cases and architecture decisions"],
        }
        return json.dumps(data, indent=2)

    def _mock_code_analysis(self, code: str) -> str:
        findings = []
        lowered = code.lower()
        if "password" in lowered and ("1234" in code or "admin" in lowered):
            findings.append({
                "id": "QF-1",
                "severity": "high",
                "category": "security",
                "evidence": "The snippet appears to contain hard-coded credentials or weak authentication logic.",
                "recommendation": "Remove hard-coded secrets, store credentials securely, and use hashed passwords with proper authentication controls.",
            })
        if "except:" in lowered:
            findings.append({
                "id": "QF-2",
                "severity": "medium",
                "category": "reliability",
                "evidence": "A broad except clause can hide unexpected failures.",
                "recommendation": "Catch specific exceptions and log safe diagnostic information.",
            })
        if not findings:
            findings.append({
                "id": "QF-1",
                "severity": "medium",
                "category": "maintainability",
                "evidence": "The snippet should be reviewed for input validation, error handling, and tests.",
                "recommendation": "Add explicit validation, expected exceptions, and unit tests for normal and boundary cases.",
            })

        data = {
            "summary": "Static mock review of the submitted code snippet.",
            "assumptions": ["The code is analyzed without executing it."],
            "detected_language": "python" if "def " in code or "import " in code else "unknown or inferred from snippet",
            "quality_findings": findings,
            "refactoring_suggestions": ["Separate validation, business logic, and persistence code where applicable."],
            "safe_test_ideas": ["Test valid input, invalid input, boundary cases, and authorization failures."],
        }
        return json.dumps(data, indent=2)

    def _mock_attack_scenarios(self, text: str) -> str:
        domain = self._domain_from_text(text)
        if domain == "study_planner":
            asset = "Student schedules, deadlines, and availability data"
            scenario = "An unauthorized user accesses or modifies another student's study plan."
            privacy = "Exposure of study habits, deadlines, and personal availability."
        elif domain == "clinic_booking":
            asset = "Patient profiles and appointment records"
            scenario = "A user attempts to view or modify another patient's appointment information."
            privacy = "Exposure of sensitive patient scheduling and medical context."
        else:
            asset = "User records and generated engineering artifacts"
            scenario = "A user attempts to access or manipulate resources belonging to another user."
            privacy = "Exposure of confidential project or personal data."

        data = {
            "threat_model_assumptions": ["The system is a web application that stores user data and exposes interactive workflows."],
            "attack_scenarios": [
                {
                    "id": "AS-1",
                    "title": "Unauthorized access to user records",
                    "asset_at_risk": asset,
                    "threat_actor": "Authenticated malicious user or external attacker",
                    "scenario": scenario,
                    "impact": "high",
                    "likelihood": "medium",
                    "mitigations": ["Enforce object-level authorization on every request.", "Use server-side ownership checks.", "Add audit logging for sensitive actions."],
                    "validation_tests": ["Verify that user A cannot read, update, or delete user B resources."],
                },
                {
                    "id": "AS-2",
                    "title": "Prompt misuse or unsafe generated recommendation",
                    "asset_at_risk": "Engineering decisions and user trust",
                    "threat_actor": "Careless or malicious user",
                    "scenario": "The assistant is asked to produce unsupported or unsafe recommendations from incomplete input.",
                    "impact": "medium",
                    "likelihood": "medium",
                    "mitigations": ["Reject insufficient input.", "Display assumptions and clarification questions.", "Require human approval for high-impact outputs."],
                    "validation_tests": ["Submit 'hi' and verify that the assistant asks for clarification instead of inventing requirements."],
                },
            ],
            "unsafe_scenarios": [
                {
                    "id": "US-1",
                    "title": "Privacy exposure",
                    "scenario": privacy,
                    "affected_users": ["End users", "System administrators"],
                    "harm": "Confidentiality loss, incorrect decisions, or misuse of personal information.",
                    "mitigations": ["Minimize stored data.", "Apply access control.", "Avoid logging sensitive input.", "Provide deletion controls where applicable."],
                    "validation_tests": ["Inspect logs and storage after submitting sensitive sample data."],
                }
            ],
            "residual_risks": ["Some domain-specific risks require expert review and cannot be fully eliminated by prompt engineering."],
        }
        return json.dumps(data, indent=2)
