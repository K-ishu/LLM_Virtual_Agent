"""Pydantic request/response schemas for the optional FastAPI backend."""

from pydantic import BaseModel, Field


class ProjectDescriptionRequest(BaseModel):
    project_description: str = Field(min_length=10)
    use_context: bool = False


class RequirementsTextRequest(BaseModel):
    requirements_text: str = Field(min_length=10)
    use_context: bool = False


class ArchitectureRequest(BaseModel):
    project_description: str = Field(min_length=10)
    requirements_text: str = Field(min_length=10)
    use_context: bool = False
