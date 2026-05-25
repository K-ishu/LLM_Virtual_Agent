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


CODE_ANALYSIS_PROMPT = """
Task: Analyze a code snippet for software engineering quality.

Code snippet:
{code_text}

Local reference context from downloaded datasets, if available:
{reference_context}

Instructions:
- Focus on defensive review, maintainability, reliability, readability, and basic security.
- Do not claim that the code is vulnerable unless the evidence is visible in the snippet.
- Do not provide exploit instructions; provide safe remediation guidance.
- If language or execution context is unclear, state assumptions.

Return valid JSON with exactly this schema:
{{
  "summary": "...",
  "assumptions": ["..."],
  "detected_language": "...",
  "quality_findings": [
    {{"id": "QF-1", "severity": "low|medium|high", "category": "bug|readability|maintainability|performance|security|privacy|reliability|other", "evidence": "...", "recommendation": "..."}}
  ],
  "refactoring_suggestions": ["..."],
  "safe_test_ideas": ["..."]
}}
""".strip()

ATTACK_SCENARIO_PROMPT = """
Task: Generate defensive attack, misuse, and unsafe scenarios for the software system.

Project description:
{project_description}

Requirements:
{requirements_text}

Local reference context from downloaded datasets, if available:
{reference_context}

Instructions:
- Generate scenarios only for defensive engineering, risk assessment, testing, and mitigation.
- Avoid operational exploit steps, real credential theft, malware, or harmful instructions.
- Include privacy, security, safety, abuse, and human-in-the-loop risks when relevant.
- Make each mitigation actionable and testable.

Return valid JSON with exactly this schema:
{{
  "threat_model_assumptions": ["..."],
  "attack_scenarios": [
    {{"id": "AS-1", "title": "...", "asset_at_risk": "...", "threat_actor": "...", "scenario": "...", "impact": "low|medium|high", "likelihood": "low|medium|high", "mitigations": ["..."], "validation_tests": ["..."]}}
  ],
  "unsafe_scenarios": [
    {{"id": "US-1", "title": "...", "scenario": "...", "affected_users": ["..."], "harm": "...", "mitigations": ["..."], "validation_tests": ["..."]}}
  ],
  "residual_risks": ["..."]
}}
""".strip()
