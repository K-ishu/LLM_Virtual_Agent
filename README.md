# LLM-Powered Virtual Assistant for Software Engineering

An academic AI Systems Engineering project that implements an LLM-powered virtual assistant for early-stage software engineering workflows.

The system helps users transform a natural-language project brief into structured software-engineering artifacts, including requirements, requirement review feedback, test cases, architecture suggestions, code-quality analysis, and defensive security scenarios.

## Project Overview

This project is designed as a human-in-the-loop software engineering assistant. The user provides a short project description, selects one workflow module, reviews the generated output, and exports the result in a documentation-ready format.

The application is implemented as a Streamlit web application with authentication, user-specific project brief history, exportable workflow results, formal evaluation, Docker containerization, Render deployment, and Kubernetes validation.

## Live Links

- **GitHub Repository:** https://github.com/K-ishu/LLM_Virtual_Agent
- **Live Application:** https://llm-virtual-agent-1.onrender.com

## Main Features

- Local login and sign-up system
- Optional email field during registration
- Duplicate username handling
- Password hashing
- Session-based authentication and logout
- User-specific project brief history
- Six AI-assisted software engineering workflow modules
- Markdown, JSON, Word, and PDF export
- Optional local dataset context
- AI chat support panel
- Formal prompt-based evaluation with 20 project briefs
- Dockerized application runtime
- Render live deployment
- Kubernetes-ready deployment manifests
- GitHub Actions CI/CD workflows

## Workflow Modules

| Module | Purpose |
|---|---|
| Requirements | Generates assumptions, clarification questions, functional requirements, non-functional requirements, and risks |
| Review | Detects ambiguity, missing acceptance criteria, contradictions, unverifiable statements, and improvement opportunities |
| Test Cases | Generates structured test cases with preconditions, steps, expected results, priority, and traceability |
| Architecture | Suggests architecture style, components, data flow, technology stack, deployment view, and security considerations |
| Code Analysis | Identifies likely technologies, quality findings, security issues, and improvement recommendations |
| Security | Generates abuse cases, security risks, privacy risks, mitigations, and validation tests |

## System Architecture

The application follows a layered architecture:

- **Presentation Layer:** Streamlit user interface, login/sign-up pages, dashboard, workflow selection, result rendering, and export buttons.
- **Application Layer:** Workflow orchestration and structured output generation.
- **Prompt Layer:** Module-specific prompt templates and workflow instructions.
- **LLM Client Layer:** OpenAI-compatible provider configuration and mock execution support.
- **Persistence Layer:** Local prototype storage for user accounts and project brief history.
- **Evaluation Layer:** Fixed prompt set and formal module-level evaluation results.
- **Deployment Layer:** Docker, Render, GitHub Actions, and Kubernetes manifests.

## Project Structure

~~~text
LLM_Virtual_Agent/
├── app/
│   ├── streamlit_app.py
│   ├── assistant_core.py
│   ├── llm_client.py
│   ├── prompts.py
│   └── schemas.py
├── data/
│   └── processed/
├── data_sources/
├── evaluation/
│   ├── evaluate_with_rubric.py
│   ├── prompt_set_20_project_briefs.json
│   ├── formal_evaluation_results.json
│   └── formal_evaluation_report.md
├── k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.example.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── requirements.txt
└── README.md
~~~

## Functional Requirements

| ID | Requirement |
|---|---|
| FR1 | The system shall allow users to create an account, log in, and log out. |
| FR2 | The system shall support account registration with username, password confirmation, duplicate username validation, and optional email. |
| FR3 | The system shall allow authenticated users to enter a natural-language software project brief. |
| FR4 | The system shall allow users to select one of six workflow modules. |
| FR5 | The system shall generate structured requirements from a project brief. |
| FR6 | The system shall review requirements for ambiguity and missing criteria. |
| FR7 | The system shall generate structured test cases. |
| FR8 | The system shall suggest software architecture and deployment views. |
| FR9 | The system shall analyze code-quality and security concerns. |
| FR10 | The system shall generate security risks, privacy risks, mitigations, and validation tests. |
| FR11 | The system shall store project brief history per authenticated user. |
| FR12 | The system shall export generated results in Markdown, JSON, Word, and PDF formats. |

## Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR1 | The system shall provide a simple and usable web interface. |
| NFR2 | The system shall support reproducible execution through mock mode and fixed evaluation prompts. |
| NFR3 | The system shall separate UI logic, assistant logic, prompts, evaluation, and deployment artifacts. |
| NFR4 | The system shall avoid committing real secrets or API keys. |
| NFR5 | The system shall be deployable locally, through Docker, on Render, and on Kubernetes. |
| NFR6 | The Kubernetes deployment shall include replicas, service discovery, health checks, ConfigMap, Secret template, and resource limits. |
| NFR7 | The system shall support exportable outputs suitable for academic documentation. |

## Evaluation

The project includes a formal prompt-based evaluation using 20 realistic software project briefs.

The evaluation covers the following metrics:

- Completeness
- Relevance
- Clarity
- Structure
- Security coverage
- Consistency

### Evaluation Results

| Workflow Module | Test Cases | Average Score | Pass Rate | Notes |
|---|---:|---:|---:|---|
| Requirements | 20 | 4.5 / 5 | 90% | Good FR/NFR separation |
| Review | 20 | 4.3 / 5 | 86% | Strong ambiguity and missing-criteria detection |
| Test Cases | 20 | 4.4 / 5 | 88% | Structured test cases with preconditions, steps, and expected results |
| Architecture | 20 | 4.0 / 5 | 80% | Useful high-level architecture, sometimes generic |
| Code Analysis | 20 | 4.1 / 5 | 82% | Good quality/security analysis; stronger with real code |
| Security | 20 | 4.25 / 5 | 85% | Good abuse-case and privacy-risk coverage |

## Local Execution

Create and activate a virtual environment:

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
~~~

Install dependencies:

~~~powershell
pip install -r requirements.txt
~~~

Run the Streamlit application:

~~~powershell
python -m streamlit run app\streamlit_app.py
~~~

Open:

~~~text
http://localhost:8501
~~~

## Docker Execution

Build the Docker image:

~~~powershell
docker build -t llm-se-assistant:local .
~~~

Run the container:

~~~powershell
docker run --rm -p 8501:8501 llm-se-assistant:local
~~~

Open:

~~~text
http://localhost:8501
~~~

## Render Deployment

The project includes a Render deployment configuration.

The live application is available at:

~~~text
https://llm-virtual-agent-1.onrender.com
~~~

Note: the current prototype uses local JSON-based runtime persistence. On free cloud deployments, user accounts created at runtime may not persist after redeploy or restart. A production version should use PostgreSQL, Supabase, Neon, or persistent storage.

## Kubernetes Deployment

The project includes Kubernetes manifests under the `k8s/` directory.

Apply the manifests:

~~~powershell
kubectl apply -f k8s/
~~~

Validate the deployment:

~~~powershell
kubectl -n llm-se-assistant get pods --show-labels
kubectl -n llm-se-assistant get svc
kubectl -n llm-se-assistant get endpoints
kubectl -n llm-se-assistant rollout status deployment/llm-se-assistant
~~~

Port-forward the service:

~~~powershell
kubectl -n llm-se-assistant port-forward svc/llm-se-assistant 8501:80
~~~

Open:

~~~text
http://localhost:8501
~~~

### Kubernetes Validation Evidence

The deployment was validated locally using Docker Desktop Kubernetes.

~~~text
Pods: two replicas running
Service: ClusterIP exposed on port 80
Endpoints: two pod endpoints mapped to port 8501
Rollout: deployment successfully rolled out
~~~

The Kubernetes deployment includes:

- Namespace
- ConfigMap
- Secret template
- Deployment
- Service
- Ingress
- Two replicas
- Readiness probe
- Liveness probe
- Resource requests and limits
- Container security context

## CI/CD

GitHub Actions workflows provide development evidence for:

- CI checks
- Docker image build and publish workflow
- Deployment-related validation
- Iterative project development history

## Security and Privacy

Implemented controls:

- Password hashing
- Local authentication
- Logout session clearing
- Duplicate username handling
- User-specific project brief history
- Secret template instead of committed real secrets
- Kubernetes security context
- No privilege escalation
- Dropped Linux capabilities

Future hardening:

- PostgreSQL-backed persistence
- Password reset
- Email verification
- MFA
- Rate limiting
- Account lockout
- Centralized secret manager
- Monitoring and structured logging

## Limitations

This project is an academic prototype. The main limitations are:

- Runtime user data is stored locally rather than in a production database.
- Render free deployment may reset runtime-created accounts after redeploy or restart.
- Evaluation is prompt-based and not yet expert-human validated.
- Code analysis currently focuses on project descriptions rather than full repository parsing.
- Kubernetes validation was performed locally using Docker Desktop Kubernetes.
- Monitoring is limited to application health checks and basic logs.

## Future Work

Planned improvements include:

- PostgreSQL or Supabase persistence
- Expert-based evaluation
- LLM-as-judge comparison
- Repository-level code analysis
- Role-based access control
- Cloud Kubernetes deployment on GKE, EKS, AKS, or a university cluster
- Prometheus and Grafana monitoring
- Structured logging and error tracking
- Multi-language support

## Academic Contribution

The project demonstrates how LLMs can support early software-engineering work by converting informal project descriptions into structured artifacts. It combines software-engineering workflow support, human-in-the-loop interaction, reproducible evaluation, and deployment readiness into one integrated academic prototype.

## Repository

~~~text
https://github.com/K-ishu/LLM_Virtual_Agent
~~~

## Live Application

~~~text
https://llm-virtual-agent-1.onrender.com
~~~
