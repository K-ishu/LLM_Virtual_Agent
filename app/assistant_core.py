"""Core assistant functions."""

from __future__ import annotations

import json
import re
from typing import Any

from app.corpus import retrieve_context
from app.llm_client import LLMClient
from app.prompts import (
    ARCHITECTURE_PROMPT,
    REQUIREMENTS_PROMPT,
    REVIEW_PROMPT,
    SYSTEM_PROMPT,
    TEST_CASE_PROMPT,
)

NO_CONTEXT = "No local corpus context provided."


def _extract_json(text: str) -> dict[str, Any]:
    """Parse JSON, with a fallback for code-fenced model outputs."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


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
