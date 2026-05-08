"""Prompt templates for the LLM-powered software engineering assistant."""

SYSTEM_PROMPT = """
You are an LLM-powered assistant for human-machine cooperation in software engineering.
Your role is to support, not replace, the human engineer.
Return structured, verifiable, concise outputs.
Do not invent facts that are not supported by the user's input or the local reference context.
When information is missing, explicitly ask clarification questions or state assumptions.
Pay attention to safety, privacy, security, fairness, maintainability, and testability.
""".strip()

REQUIREMENTS_PROMPT = """
Task: Generate software requirements from the project description.

Project description:
{project_description}

Local reference context from downloaded datasets, if available:
{reference_context}

Instructions:
- Use the local reference context only as examples of requirement style and possible concerns.
- Do not copy long passages from the context.
- Do not assume that context facts are true for the user's project unless supported by the project description.

Return valid JSON with exactly this schema:
{{
  "assumptions": ["..."],
  "clarification_questions": ["..."],
  "functional_requirements": [
    {{"id": "FR-1", "requirement": "The system shall ...", "rationale": "..."}}
  ],
  "non_functional_requirements": [
    {{"id": "NFR-1", "quality_attribute": "security|privacy|performance|usability|reliability|maintainability|scalability|other", "requirement": "The system shall ...", "rationale": "..."}}
  ],
  "risks": ["..."]
}}
""".strip()

REVIEW_PROMPT = """
Task: Review the requirements for quality issues.

Requirements:
{requirements_text}

Local reference context from downloaded datasets, if available:
{reference_context}

Check for ambiguity, incompleteness, inconsistency, unverifiable wording, privacy/security risks, missing edge cases, and missing acceptance criteria.
Use the local context only as supporting examples of requirement quality concerns.

Return valid JSON with exactly this schema:
{{
  "summary": "...",
  "issues": [
    {{"id": "ISSUE-1", "severity": "low|medium|high", "type": "ambiguity|incomplete|inconsistent|unverifiable|security|privacy|safety|other", "evidence": "...", "recommendation": "..."}}
  ],
  "improved_requirements": ["..."],
  "clarification_questions": ["..."]
}}
""".strip()

TEST_CASE_PROMPT = """
Task: Generate test cases from the requirements.

Requirements:
{requirements_text}

Local reference context from downloaded datasets, if available:
{reference_context}

Return valid JSON with exactly this schema:
{{
  "test_cases": [
    {{
      "id": "TC-1",
      "related_requirement_ids": ["FR-1"],
      "title": "...",
      "preconditions": ["..."],
      "steps": ["..."],
      "expected_result": "...",
      "priority": "low|medium|high",
      "test_type": "functional|security|privacy|performance|usability|negative|other"
    }}
  ],
  "coverage_notes": ["..."],
  "missing_information": ["..."]
}}
""".strip()

ARCHITECTURE_PROMPT = """
Task: Propose a simple architecture for the software system.

Project description:
{project_description}

Requirements:
{requirements_text}

Local reference context from downloaded datasets, if available:
{reference_context}

Return valid JSON with exactly this schema:
{{
  "architecture_style": "...",
  "components": [
    {{"name": "...", "responsibility": "...", "inputs": ["..."], "outputs": ["..."]}}
  ],
  "data_flow": ["..."],
  "technology_stack": ["..."],
  "deployment_view": "...",
  "security_privacy_considerations": ["..."],
  "human_in_the_loop_points": ["..."]
}}
""".strip()
