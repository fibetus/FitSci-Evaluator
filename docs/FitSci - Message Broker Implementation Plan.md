# FitSci - Message Broker Implementation Plan (RabbitMQ)

**Status:** Planned
**Target Phase:** Phase 2 (Async API Integration)
**Related ADR:** [ADR-0006](./adr/0006-message-broker-rabbitmq.md)

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

1. **Unit Tests:** Mock `MessageQueuePort` in the FastAPI endpoint tests to ensure messages are dispatched.
2. **Integration Tests:** Use `testcontainers-rabbitmq` (or a local Docker instance) to test the `RabbitMQAdapter`'s publish and consume logic end-to-end.
3. **Resilience Testing:** Kill the worker process mid-evaluation and verify the message is redelivered when the worker restarts.

## 5. Infrastructure & Deployment

1. **Docker Compose:** Update `docker-compose.yml` to include a `rabbitmq:3-management` service alongside PostgreSQL.
2. **Environment Variables:** Add `RABBITMQ_URL` to `.env.example` and the config schema.
3. **Worker Service:** The deployment configuration (e.g., systemd or docker-compose) must now run two services for the backend: `api` (FastAPI) and `worker` (Consumer).

## 6. Definition of Done
- [ ] `ADR-0006` is merged and accepted.
- [ ] `MessageQueuePort` is defined.
- [ ] `RabbitMQAdapter` is implemented and unit tested.
- [ ] Separate `worker` entrypoint is created and can consume messages.
- [ ] FastAPI `POST /evaluate` pushes messages instead of running inference directly.
- [ ] End-to-end integration test passes: HTTP POST -> RabbitMQ -> Worker -> Postgres -> HTTP GET results.
