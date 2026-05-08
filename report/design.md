# Design Document

## 1. Project Type

Innovation-driven project with an evaluation component.

## 2. Stakeholders

- Software engineering students
- Junior software developers
- Requirements engineers
- QA/test engineers
- Course evaluator/teacher

## 3. Stakeholder Needs

- Convert informal project descriptions into structured requirements.
- Detect ambiguous, incomplete, inconsistent, or unverifiable requirements.
- Generate traceable test cases from requirements.
- Suggest a simple architecture that a human can inspect and revise.
- Preserve human control over final engineering decisions.
- Use online datasets in a reproducible way without requiring live web access during demonstration.

## 4. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | The system shall accept a project description from the user. |
| FR-2 | The system shall generate functional requirements. |
| FR-3 | The system shall generate non-functional requirements. |
| FR-4 | The system shall review requirements for ambiguity, incompleteness, inconsistency, and unverifiable wording. |
| FR-5 | The system shall generate test cases with traceability to requirements. |
| FR-6 | The system shall suggest a high-level system architecture. |
| FR-7 | The system shall allow the human user to revise inputs and rerun tasks. |
| FR-8 | The system shall download selected public datasets into a local raw-data folder. |
| FR-9 | The system shall prepare a local processed corpus and evaluation set from the downloaded data. |
| FR-10 | The system shall optionally retrieve relevant local context for the LLM from the processed corpus. |

## 5. Non-Functional Requirements

| ID | Quality Attribute | Requirement |
|---|---|---|
| NFR-1 | Usability | Outputs shall be structured as readable JSON and displayed in the UI. |
| NFR-2 | Privacy | The system shall keep API keys in environment variables and shall not intentionally expose them in outputs. |
| NFR-3 | Reproducibility | The system shall provide Docker-based local deployment and fixed data-preparation scripts. |
| NFR-4 | Maintainability | Prompts, assistant logic, corpus retrieval, data scripts, and evaluation scripts shall be separated into modules. |
| NFR-5 | Safety | The system shall state assumptions and clarification questions when information is missing. |
| NFR-6 | Robustness | The prototype shall run in mock mode without paid API access. |
| NFR-7 | Data stability | The runtime assistant shall use local processed data rather than live web crawling. |

## 6. Architecture

```text
Online public datasets
  |
  v
Data Download Script
  |
  v
data/raw/
  |
  v
Benchmark Preparation Script
  |
  v
data/processed/ -----> Local Corpus Retriever
                         |
User                     v
  |                 Reference Context
  v                      |
Streamlit UI -----------+
  |
  v
Assistant Core
  |
  +--> Prompt Templates
  |
  +--> LLM Client
  |       |
  |       +--> Mock Provider
  |       +--> OpenAI-Compatible Provider
  |
  +--> JSON Parser / Validator
  |
  v
Structured Output
  |
  v
Evaluation Scripts
```

## 7. Design Choices

- Streamlit is used for a fast local prototype.
- FastAPI is included as an optional backend for API-based interaction.
- Prompt templates are versioned to make experiments reproducible.
- Mock mode supports local demonstration without paid API access.
- Docker supports local deployment.
- Online datasets are downloaded once and converted into local JSONL/JSON artifacts.
- Local retrieval uses TF-IDF similarity over the processed corpus, with a token-overlap fallback.

## 8. Human-Machine Cooperation

The assistant does not make final engineering decisions. Human users review:

- generated requirements;
- detected quality issues;
- generated test cases;
- proposed architecture;
- assumptions and clarification questions;
- retrieved local context when context mode is enabled.

## 9. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Hallucinated requirements | Force assumptions and clarification questions in the prompt; keep human approval. |
| Incomplete test coverage | Evaluate traceability and missing information. |
| Privacy leakage | Avoid persistent logging of user input; use environment variables for credentials. |
| Low reproducibility | Provide Dockerfile, dataset scripts, fixed prompts, and local processed benchmark. |
| Live-web instability | Do not crawl websites during normal runtime; download datasets once. |
| Dataset licensing uncertainty | Keep user-story licensing notes and avoid redistributing manually downloaded restricted data. |

## DevOps and Deployment Design

The deployment architecture uses containerization and cloud-native infrastructure:

```text
Developer push
    ↓
GitHub Actions CI
    ↓
Unit tests + mock evaluation + Docker build
    ↓
GitHub Container Registry
    ↓
Render deployment or Kubernetes deployment
```

### Docker

The Docker image packages the Streamlit prototype, Python dependencies, prompt logic, local retrieval code, and evaluation-ready data structure. The container reads the web port from the `PORT` environment variable, supports mock mode by default, and exposes the Streamlit health endpoint.

### CI/CD

The CI workflow verifies that the project remains executable and reproducible. The publishing workflow builds an immutable Docker image and pushes it to GitHub Container Registry. Deployment to Render is handled by `render.yaml` and can also be triggered by a Render deploy hook. Kubernetes deployment is controlled by a manual workflow to avoid accidental cloud changes.

### Kubernetes

The Kubernetes manifests define a Namespace, ConfigMap, Secret template, Deployment, Service, and Ingress. The Deployment uses readiness and liveness probes to support safe rollout and recovery.

### Cloud Deployment

Render is selected as the primary simple cloud target because it can build directly from the repository's Dockerfile and use a Blueprint file as infrastructure-as-code. Kubernetes is included as the advanced deployment target for demonstrating orchestration, rollout, and cloud-native deployment.
