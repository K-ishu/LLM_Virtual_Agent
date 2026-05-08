# Kubernetes Deployment

These manifests deploy the Streamlit-based LLM Software Engineering Assistant.

## 1. Build and push image

Use the GitHub Actions `Build and Publish Docker Image` workflow, or build manually:

```bash
docker build -t ghcr.io/<owner>/<repo>:latest .
docker push ghcr.io/<owner>/<repo>:latest
```

## 2. Configure image

Edit `k8s/deployment.yaml` and replace:

```text
ghcr.io/OWNER/REPOSITORY:latest
```

with your real image name, or deploy through the `Deploy to Kubernetes` GitHub Actions workflow and provide the image input.

## 3. Optional secret for real LLM calls

The default ConfigMap uses mock mode. For OpenAI-compatible calls:

```bash
kubectl apply -f k8s/namespace.yaml
cp k8s/secret.yaml.example k8s/secret.yaml
# edit k8s/secret.yaml and set OPENAI_API_KEY
kubectl apply -f k8s/secret.yaml
kubectl -n llm-se-assistant set env deployment/llm-se-assistant LLM_PROVIDER=openai
```

Do not commit `k8s/secret.yaml`.

## 4. Apply manifests

```bash
kubectl apply -f k8s/
kubectl -n llm-se-assistant rollout status deployment/llm-se-assistant
```

## 5. Local port-forward test

```bash
kubectl -n llm-se-assistant port-forward svc/llm-se-assistant 8501:80
```

Open `http://localhost:8501`.

## 6. Ingress

Update `k8s/ingress.yaml` with your real hostname and make sure an Ingress controller is installed in the cluster.
