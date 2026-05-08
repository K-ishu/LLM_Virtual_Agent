# LLM-Powered Virtual Assistant for Software Engineering Tasks

This repository is a course-project prototype for an **LLM-powered virtual assistant for human-machine cooperation** in software engineering.

The project follows the course workflow:

1. Requirements analysis
2. Design and architecture
3. Prototype development
4. Testing and evaluation
5. Local deployment with Docker

## Use Case

The assistant helps a human user with early software-engineering tasks:

- generate functional and non-functional requirements from a project idea;
- review requirements for ambiguity, incompleteness, inconsistency, and unverifiable wording;
- generate structured test cases from requirements;
- suggest a simple software architecture;
- keep the human user in control through review and refinement.

## Data Strategy

The project uses **online datasets, downloaded once and stored locally**. The runtime system does not depend on live web crawling. This makes the project reproducible and easier to evaluate.

```text
Online public datasets
        ↓
data_sources/download_datasets.py
        ↓
data/raw/
        ↓
data_sources/prepare_benchmark.py
        ↓
data/processed/
        ↓
Local retrieval context + evaluation benchmark
```

The Streamlit UI has an optional **Use local dataset context** checkbox. When enabled, the assistant retrieves the most relevant examples from `data/processed/` and passes them to the LLM as local reference context.

## Online Data Sources

The project is configured for these public requirements-engineering/security sources:

- PURE requirements dataset: https://zenodo.org/records/1414117
- User stories requirements dataset: https://zenodo.org/records/13880060
- FR/NFR requirements dataset: https://data.mendeley.com/datasets/4ysx9fyzv4/1
- OWASP user security stories: https://github.com/OWASP/user-security-stories

Use the data only according to each source's license and terms. Some user-story datasets include curator notes about uncertain upstream licensing; use them for academic experimentation with proper citation and avoid redistributing modified copies unless permitted.

## Quick Start Without an API Key

The app can run in mock mode for UI and pipeline testing.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python data_sources/prepare_benchmark.py
streamlit run app/streamlit_app.py
```

`prepare_benchmark.py` creates a small processed corpus from the included seed examples even before online datasets are downloaded.

## Download Online Data

```bash
python data_sources/download_datasets.py
python data_sources/prepare_benchmark.py
```

Downloaded files are stored under `data/raw/`. Processed benchmark examples are stored under `data/processed/`.

For the FR/NFR Mendeley dataset, follow the manual note written to:

```text
data/raw/fr_nfr_dataset/README_MANUAL_DOWNLOAD.md
```

Then rerun:

```bash
python data_sources/prepare_benchmark.py
```

## Quick Start With an OpenAI-Compatible LLM

Edit `.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=
```

Then run:

```bash
streamlit run app/streamlit_app.py
```

For local OpenAI-compatible servers such as Ollama, LM Studio, or vLLM, set `OPENAI_BASE_URL` and a compatible model name.

## Run Evaluation

Without retrieval context:

```bash
python evaluation/evaluate_with_rubric.py --input data/processed/eval_set.json --output data/processed/evaluation_results.json
```

With retrieval context:

```bash
python evaluation/evaluate_with_rubric.py --input data/processed/eval_set.json --output data/processed/evaluation_results_with_context.json --use-context
```

## Docker Deployment

```bash
docker compose up --build
```

Then open the Streamlit URL printed in the terminal.

## Repository Structure

```text
llm_virtual_assistant_project/
├── app/
│   ├── streamlit_app.py
│   ├── api.py
│   ├── assistant_core.py
│   ├── corpus.py
│   ├── llm_client.py
│   ├── prompts.py
│   └── schemas.py
├── data/
│   ├── seed_requirements_examples.jsonl
│   ├── raw/
│   └── processed/
├── data_sources/
│   ├── DATA_SOURCES.md
│   ├── download_datasets.py
│   └── prepare_benchmark.py
├── evaluation/
│   └── evaluate_with_rubric.py
├── tests/
│   └── test_core_mock.py
├── report/
│   ├── design.md
│   └── evaluation_plan.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```



## DevOps, CI/CD, Cloud, and Kubernetes

The repository now includes a complete deployment stack:

- **Dockerfile**: production-style Streamlit container with non-root user and health check.
- **docker-compose.yml**: local reproducible deployment.
- **render.yaml**: Render Blueprint for cloud deployment with Docker.
- **GitHub Actions**:
  - `ci.yml` for tests, evaluation, and Docker build;
  - `docker-publish.yml` for publishing images to GitHub Container Registry;
  - `k8s-deploy.yml` for manual Kubernetes rollout.
- **Kubernetes manifests** under `k8s/`:
  - Namespace;
  - ConfigMap;
  - Secret template;
  - Deployment;
  - Service;
  - Ingress.

Detailed instructions are in:

```text
docs/deployment.md
docs/ci_cd.md
k8s/README.md
```

### Local Docker smoke test

```bash
./scripts/local_smoke_test.sh
```

### Render deployment

Push the repository to GitHub and create a Render Blueprint from `render.yaml`. The default deployment runs in `mock` mode. For real LLM calls, set `LLM_PROVIDER=openai` and add `OPENAI_API_KEY` in Render's secret environment variables.

### Kubernetes deployment

```bash
kubectl apply -f k8s/
kubectl -n llm-se-assistant rollout status deployment/llm-se-assistant
kubectl -n llm-se-assistant port-forward svc/llm-se-assistant 8501:80
```

Before using Kubernetes in a real cluster, replace the placeholder image in `k8s/deployment.yaml` or deploy via the GitHub Actions Kubernetes workflow.

## Reproducibility Notes

- Prompts are versioned in `app/prompts.py`.
- Data download scripts record a manifest in `data/raw/sources_manifest.json`.
- Runtime retrieval uses only the local processed corpus.
- Evaluation outputs are saved in JSON format.
- Docker supports local deployment.
