# FitSci - Message Broker Implementation Plan (RabbitMQ)

**Status:** Implemented (Phase 2)
**Target Phase:** Phase 2 (Async API Integration)
**Related ADR:** [ADR-0006](../adr/0006-message-broker-rabbitmq.md)

## 1. Goal

Integrate a RabbitMQ message broker to decouple the FastAPI server from the heavy computational workload of the Gemma 4 evaluator. This ensures the API remains highly responsive, avoids timeouts, and allows sequential processing of LLM requests to prevent VPS resource exhaustion (Ollama VRAM limits).

## 2. Hexagonal Architecture Additions

We will implement this by adhering to our Hexagonal architectural rules: creating a pure domain protocol (Port) and an external infrastructure implementation (Adapter).

### 2.1. The Port: `domain/ports/message_queue.py`
Create a protocol `MessageQueuePort` (or `JobQueuePort`) that defines the contract for our broker.

```python
from typing import Protocol

class MessageQueuePort(Protocol):
    async def publish_evaluation_job(self, job_id: str, pmc_id: str) -> None:
        """Publishes a new evaluation job to the queue."""
        ...
```

### 2.2. The Adapter: `adapters/broker/rabbitmq_adapter.py`
Implement `RabbitMQAdapter` using a library like `aio-pika`. This adapter will handle connection pooling, channels, and message serialization.

```python
class RabbitMQAdapter(MessageQueuePort):
    def __init__(self, amqp_url: str):
        # Setup connection details
        pass
        
    async def publish_evaluation_job(self, job_id: str, pmc_id: str) -> None:
        # Publish logic to a specific RabbitMQ exchange/queue
        pass
```

## 3. Workflow & Application Layer Changes

### 3.1. API Ingestion (FastAPI)
Currently, FastAPI is planned to handle evaluations. We must split the workflow.
- **Route:** `POST /api/v1/evaluate`
- **Action:** 
  1. Create a `Job` record in `PostgresStudyRepository` with status `PENDING`.
  2. Call `message_queue_port.publish_evaluation_job(job_id, pmc_id)`.
  3. Immediately return HTTP `202 Accepted` with the `job_id`.

### 3.2. Background Worker Process
We need a new standalone application root (e.g., `backend/src/worker/main.py`) that will act as the RabbitMQ consumer.
- **Action:**
  1. Connects to RabbitMQ and listens to the evaluation queue.
  2. Upon receiving a message containing `job_id` and `pmc_id`, updates job status to `RUNNING`.
  3. Executes the existing `EvaluateStudyUseCase`.
  4. Updates job status to `COMPLETED` (saving the `Study` JSON) or `FAILED`.
  5. Acknowledges (`ack`) the message to RabbitMQ. If Ollama crashes, the message is unacknowledged (`nack`) and requeued.

## 4. Testing Strategy

1. **Unit Tests:** `MessageQueuePort` is faked with `InMemoryMessageQueue` in the
   endpoint/use-case tests (`test_api_evaluate.py`, `test_submit_evaluation.py`,
   `test_process_evaluation_job.py`) to assert messages are dispatched and job
   state transitions are correct. These run in CI on every push.
2. **Integration Tests:** `testcontainers[rabbitmq]` spins up a real
   `rabbitmq:3.13-management-alpine` to test the `RabbitMQAdapter` publish/consume
   roundtrip (`tests/integration/test_rabbitmq_adapter.py`).
3. **Resilience Testing:** Two cases are covered without restarting the process:
   - `test_rabbitmq_requeues_on_transient_failure` — a handler that raises is
     nacked + requeued and redelivered to the still-running consumer until it
     succeeds.
   - `test_rabbitmq_drops_malformed_message_without_requeue_loop` — a poison
     (non-JSON) message is rejected without requeue, so it cannot hot-loop.
4. **End-to-end:** `tests/integration/test_evaluate_e2e.py` drives the real
   `HTTP POST -> RabbitMQ -> Worker -> Postgres -> HTTP GET` chain with real broker
   and database containers. The LLM (Ollama/Gemma) is faked here on purpose — the
   broker DoD is about async plumbing; extraction quality is verified by the
   benchmark harness and `GemmaOllamaAdapter` unit tests.

> **Gating note:** All integration/e2e tests require Docker and are skipped unless
> `FITSCI_INTEGRATION=1`. CI currently runs `-m "not integration"`, so these are
> *not* executed on every push yet — they must be run manually (or in a dedicated
> Docker-enabled CI job) before declaring the phase verified.

## 5. Infrastructure & Deployment

1. **Docker Compose:** Update `docker-compose.yml` to include a `rabbitmq:3-management` service alongside PostgreSQL.
2. **Environment Variables:** Add `RABBITMQ_URL` to `.env.example` and the config schema.
3. **Worker Service:** The deployment configuration (e.g., systemd or docker-compose) must now run two services for the backend: `api` (FastAPI) and `worker` (Consumer).

## 6. Definition of Done
- [x] `ADR-0006` is merged and accepted.
- [x] `MessageQueuePort` is defined.
- [x] `RabbitMQAdapter` is implemented, with an integration roundtrip test and
      resilience (requeue / poison-message) tests.
- [x] Separate `worker` entrypoint is created and can consume messages.
- [x] FastAPI `POST /evaluate` pushes messages instead of running inference directly.
- [x] End-to-end integration test exists: HTTP POST -> RabbitMQ -> Worker -> Postgres
      -> HTTP GET (`tests/integration/test_evaluate_e2e.py`, LLM faked).

> **Honesty note (2026-06-26 audit):** the integration/e2e tests above are
> Docker-gated (`FITSCI_INTEGRATION=1`) and do **not** run in the default CI job
> (`-m "not integration"`). To call Phase 2 *verified* rather than merely
> *implemented*, run the full integration suite against Docker (locally or in a
> dedicated CI job) and record the result.
