# Deployment Guide

This project supports three deployment levels:

1. **Docker Compose** for local reproducibility.
2. **Render** for a simple public cloud deployment.
3. **Kubernetes** for container orchestration and a stronger DevOps demonstration.

The application is a Streamlit web app. It binds to `0.0.0.0` and reads the port from the `PORT` environment variable so it can run locally, on Render, and in Kubernetes.

## Local Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:8501`.

Health endpoint:

```bash
curl http://localhost:8501/_stcore/health
```

## Render Deployment

The repository includes `render.yaml`, so Render can create the service as infrastructure-as-code.

Default Render behavior:

- service type: web
- runtime: Docker
- health check path: `/_stcore/health`
- default mode: `LLM_PROVIDER=mock`
- secret prompt: `OPENAI_API_KEY`

Steps:

1. Push the repository to GitHub.
2. In Render, create a new Blueprint from the repository.
3. Confirm the service defined in `render.yaml`.
4. Keep `LLM_PROVIDER=mock` for demo mode, or set `LLM_PROVIDER=openai` and provide `OPENAI_API_KEY` in the Render dashboard.
5. Deploy.

The Dockerfile already uses `${PORT:-8501}`. Render normally provides `PORT=10000`, which is also set explicitly in `render.yaml`.

## GitHub Actions CI/CD

Workflows:

- `.github/workflows/ci.yml`: installs dependencies, prepares the deterministic benchmark, runs tests, runs mock evaluation, and builds the Docker image.
- `.github/workflows/docker-publish.yml`: builds and pushes the image to GitHub Container Registry on `main` and version tags.
- `.github/workflows/k8s-deploy.yml`: manually deploys an image to a Kubernetes cluster using a base64 kubeconfig secret.

Required repository secrets:

| Secret | Required for | Description |
|---|---|---|
| `RENDER_DEPLOY_HOOK_URL` | Optional Render CD | Deploy hook URL from Render. Not needed if Render auto-deploys from Git. |
| `KUBE_CONFIG_BASE64` | Kubernetes CD | Base64-encoded kubeconfig for the target cluster. |

Create `KUBE_CONFIG_BASE64` locally:

```bash
base64 -w 0 ~/.kube/config
```

On macOS:

```bash
base64 ~/.kube/config | tr -d '\n'
```

## Kubernetes Deployment

Apply manifests:

```bash
kubectl apply -f k8s/
kubectl -n llm-se-assistant rollout status deployment/llm-se-assistant
```

Before production use, replace the placeholder image in `k8s/deployment.yaml`:

```text
ghcr.io/OWNER/REPOSITORY:latest
```

or use the manual GitHub Actions Kubernetes workflow and pass the full image reference.

Port-forward for local validation:

```bash
kubectl -n llm-se-assistant port-forward svc/llm-se-assistant 8501:80
```

## Production Notes

- Use `mock` mode for public demos without exposing an API key.
- Store API keys only in Render secrets, GitHub Actions secrets, or Kubernetes Secrets.
- Keep downloaded datasets versioned or reproducibly generated; do not depend on live crawling during evaluation.
- Use the CI mock evaluation output as a baseline artifact for the course report.
