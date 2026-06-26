# 0007. Orchestrate Infrastructure (PostgreSQL, RabbitMQ, Ollama) with Docker Compose

Date: 2026-06-26
Status: Accepted

## Context

FitSci-Evaluator depends on three long-running infrastructure services, each already
the subject of its own decision:

- **PostgreSQL** — persistence for the `Study` aggregate and evaluation jobs ([ADR-0003](./0003-database-postgres-jsonb.md)).
- **RabbitMQ** — message broker decoupling the API from heavy LLM inference ([ADR-0006](./0006-message-broker-rabbitmq.md)).
- **Ollama** — local runtime serving Gemma 4 for extraction ([ADR-0004](./0004-gemma4-12b-q4km.md)).

We need a single, reproducible way to:

1. Stand these services up for **local development** with one command.
2. Deploy the same topology to a **single VPS** (the chosen production target — see ADR-0006).
3. Pin service versions so local, CI, and prod do not drift.
4. Gate application startup until its dependencies are actually healthy (avoid
   races where the API/worker connect before Postgres or RabbitMQ are ready).
5. Keep the developer's inner loop fast: run infra in containers while the Python
   app runs on the host (for debugging), *or* run the whole stack in containers.

Without orchestration, each contributor would install and version these services
by hand — the exact doc/code drift the project's audits flagged as the #1 risk.

## Decision

We use a **single `docker-compose.yml`** at the repository root as the source of
truth for infrastructure topology.

### Services and pinned images
- `postgres` → `postgres:16-alpine`
- `rabbitmq` → `rabbitmq:3.13-management-alpine` (management UI included)
- `ollama` → `ollama/ollama:0.30.10`
- `migrate`, `api`, `worker` → built from `backend/Dockerfile` (the application)

### Profiles separate "infra" from "app"
- Default (no profile): only `postgres`, `rabbitmq`, `ollama` start. This is the
  **infra-only** mode — the app runs on the host (`uv run ...`). Best for development.
- `--profile app`: additionally starts `migrate`, `api`, and `worker` in containers
  for a full in-Docker stack.

### Health gating
Every infra service declares a `healthcheck`. App services use
`depends_on: { condition: service_healthy }` for `postgres`/`rabbitmq` and
`condition: service_completed_successfully` for the one-shot `migrate` service, so
the API and worker never start before migrations have run against a healthy database.

### Local ↔ VPS via environment variables
Connection details are component env vars (`POSTGRES_HOST`, `RABBITMQ_HOST`,
`OLLAMA_BASE_URL`, …) resolved by `Settings` (see `backend/src/config/settings.py`).
The same compose file serves both modes: `FITSCI_DEPLOYMENT=local` points at the
compose network; `vps` points the host vars at a remote server. Named volumes
(`postgres_data`, `rabbitmq_data`, `ollama_data`) persist state across restarts.

## Alternatives considered

- **Bare-metal / manual install** of Postgres, RabbitMQ, and Ollama per machine —
  rejected: non-reproducible, version drift, slow onboarding, the documented #1 risk.
- **Kubernetes / k3s** — rejected for the same reason RabbitMQ was chosen over Kafka
  in ADR-0006: the target is a single VPS, and the operational overhead (control
  plane, manifests, ingress) is unjustified at this scale. Revisit only if we move
  to multi-node.
- **Managed cloud services** (e.g. RDS, CloudAMQP, a hosted LLM API) — rejected:
  cost for a hackathon/VPS target, and a hosted closed-weights LLM would violate the
  Gemma-4 brief locked in ADR-0004.
- **Separate compose files per concern** — rejected: profiles express the
  infra/app split inside one file without multiplying files or `-f` flags.

## Consequences

**Positive**
- `docker compose up -d` brings up all infra in one command; `--profile app` brings
  up the full stack. Helper scripts (`scripts/dev.sh`, `scripts/dev.ps1`) wrap this.
- Pinned images make local, CI, and prod reproducible.
- Health gating removes connect-before-ready races for API and worker.
- One file works for both local and VPS by changing env vars only.
- testcontainers-based integration tests reuse the same pinned images
  (`postgres:16-alpine`, `rabbitmq:3.13-management-alpine`; Ollama uses the same
  `ollama/ollama:0.30.10` tag via compose), keeping test infra faithful to runtime.

**Negative / trade-offs**
- The `ollama` container is **not** GPU-accelerated by default; on a GPU VPS you
  typically run Ollama on the host and set `OLLAMA_BASE_URL` to it (or add GPU
  device reservations to the service). This is a deliberate per-deployment choice,
  not a default.
- Compose is single-host. Horizontal scale-out (multiple workers across nodes)
  would require a different orchestrator and a new ADR.
- Docker becomes a hard prerequisite for development and for the integration test
  suite.

**Neutral**
- `migrate` is a one-shot job, not a daemon; it must exit 0 before `api`/`worker`
  start. Schema changes therefore flow through Alembic, consistent with ADR-0003.
