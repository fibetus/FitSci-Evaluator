#!/usr/bin/env bash
# Start FitSci local infrastructure (PostgreSQL, RabbitMQ, Ollama).
# Usage: ./scripts/dev.sh up|down|logs|migrate|pull-model|status

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CMD="${1:-up}"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "[*] Created .env from .env.example — review credentials before VPS deploy."
fi

case "$CMD" in
  up)
    docker compose up -d
    cat <<'EOF'

[*] Infra running. Next steps:
    cd backend
    uv sync
    uv run alembic upgrade head
    uv run pytest -m "not integration"

    Pull Gemma model: ./scripts/dev.sh pull-model
    API in Docker:    docker compose --profile app up -d --build
EOF
    ;;
  down)
    docker compose --profile app down || true
    docker compose down
    ;;
  logs)
    docker compose logs -f postgres rabbitmq ollama
    ;;
  migrate)
    (cd backend && uv run alembic upgrade head)
    ;;
  pull-model)
    MODEL="$(grep -E '^GEMMA_MODEL_TAG=' .env | cut -d= -f2- || true)"
    MODEL="${MODEL:-gemma4:12b-q4_k_m}"
    docker compose exec ollama ollama pull "$MODEL"
    ;;
  status)
    docker compose ps
    ;;
  *)
    echo "Usage: $0 up|down|logs|migrate|pull-model|status" >&2
    exit 1
    ;;
esac
