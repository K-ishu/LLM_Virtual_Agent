# CI/CD Design

The CI/CD pipeline is designed to support the course requirements for reproducibility, testing, deployment, and presentation.

## Pipeline Stages

```text
Git push / pull request
        ↓
Install dependencies
        ↓
Prepare deterministic benchmark
        ↓
Run unit tests in mock mode
        ↓
Run mock evaluation
        ↓
Build Docker image
        ↓
Push image to GitHub Container Registry
        ↓
Deploy to Render or Kubernetes
```

## CI

The CI workflow blocks integration if:

- Python dependencies cannot be installed;
- the benchmark preparation fails;
- unit tests fail;
- the mock evaluation script fails;
- the Docker image cannot be built.

## CD to Render

Render can auto-deploy from the Git repository using `render.yaml`. Optionally, GitHub Actions can trigger a Render deploy hook after the image publishing workflow.

## CD to Kubernetes

Kubernetes deployment is manual by default through `workflow_dispatch`. This is safer for a course project because it avoids deploying every commit to a paid or limited cluster.
