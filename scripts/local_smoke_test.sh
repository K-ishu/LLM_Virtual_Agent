#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-llm-se-assistant:smoke}"
CONTAINER="${CONTAINER:-llm-se-assistant-smoke}"
PORT="${PORT:-8501}"

docker build -t "$IMAGE" .
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER" -p "$PORT:$PORT" -e PORT="$PORT" -e LLM_PROVIDER=mock "$IMAGE"

for i in {1..30}; do
  if curl -fsS "http://localhost:$PORT/_stcore/health" >/dev/null; then
    echo "Smoke test passed: http://localhost:$PORT/_stcore/health"
    docker rm -f "$CONTAINER" >/dev/null
    exit 0
  fi
  sleep 2
done

docker logs "$CONTAINER"
docker rm -f "$CONTAINER" >/dev/null
exit 1
