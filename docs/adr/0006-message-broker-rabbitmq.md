# 0006. Message Broker for Asynchronous LLM Evaluation (RabbitMQ)

Date: 2026-06-24
Status: Accepted

## Context

The FitSci-Evaluator system uses a local LLM (Gemma 4 via Ollama) to extract structured data from research papers. LLM inference is computationally expensive and slow (can take over 60 seconds per paper). 

If we process evaluations synchronously within the FastAPI request lifecycle, we face severe scalability issues:
1. **Blocking Requests:** A single user uploading a PDF or requesting a PMCID evaluation will keep the HTTP connection open and block until the Ollama inference is done.
2. **Concurrency Bottleneck:** If two users request an evaluation simultaneously, Ollama (especially on a local VPS) will either queue them internally without user feedback or crash due to VRAM limits. FastAPI would be unaware of the LLM's state.
3. **Timeouts:** Long-running evaluations will trigger HTTP timeouts on the client or reverse proxy side.

We need a way to decouple the ingestion of an evaluation request from the actual LLM processing. We evaluated **RabbitMQ** and **Apache Kafka** for this role.

## Decision

We will introduce a **Message Broker** to handle asynchronous evaluation requests, and we specifically choose **RabbitMQ**.

### Why a Message Broker?
When a user submits a study (PMCID or PDF), FastAPI will immediately construct a job, save its "Pending" state in the database, and **publish a message** to the broker. The API immediately returns a `202 Accepted` to the user. A separate background worker process consumes these messages one by one, invoking the local Ollama instance sequentially. Once finished, the worker updates the job status in the database and optionally publishes a "Completion" event.

### Why RabbitMQ over Kafka?
- **Task Queuing vs. Event Streaming:** RabbitMQ is explicitly designed for task routing and work queues (AMQP). Kafka is an append-only distributed event log. We need simple task queuing (dispatching a job to an available worker and acknowledging it once done).
- **Complexity and Overhead:** Kafka requires more infrastructure setup, memory, and operational overhead. RabbitMQ is lightweight and perfectly suited for our single-VPS deployment target.
- **Message Acknowledgment:** RabbitMQ's strict acknowledgment model ensures that if a worker crashes mid-evaluation (e.g., Ollama runs out of memory), the message is requeued and not lost.

## Consequences

- **New Port:** We will introduce a new port, e.g., `JobQueuePort` or `MessageBrokerPort` in `domain/ports/`.
- **New Adapter:** We will implement `adapters/broker/rabbitmq_adapter.py` integrating the `aio-pika` or `pika` library.
- **Worker Process:** We must deploy a separate worker process alongside the FastAPI server that continuously consumes from RabbitMQ and runs the `EvaluateStudyUseCase`.
- **Infrastructure:** RabbitMQ must be added to the local development environment (via Docker) and production VPS.
- **User Experience:** The frontend must poll the `/jobs/{id}` endpoint or subscribe to WebSockets to get the final evaluation result, since the initial HTTP request will no longer return the score directly.
