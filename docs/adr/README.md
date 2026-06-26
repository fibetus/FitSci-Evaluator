# Architecture Decision Records (ADRs)

This folder records the architectural decisions that shape **FitSci - Evaluator**. Every architectural decision that affects more than one module belongs here, in chronological order.

## Format

We use a lightweight **MADR-flavored** template (see [adr.github.io](https://adr.github.io/madr/)):

* **Status** — Proposed · Accepted · Superseded · Deprecated.
* **Context** — what motivated this decision.
* **Decision** — what was decided.
* **Alternatives considered** — what was evaluated and rejected.
* **Consequences** — positive, negative, neutral.

## Index

| # | Title | Status | Date |
|---|---|---|---|
| [0001](./0001-architecture-hexagonal.md) | Adopt Hexagonal (Ports & Adapters) architecture | Accepted | 2026-05-06 |
| [0002](./0002-scoring-canonical-spec.md) | `scoring_basis.md` is the canonical spec for the implemented Judge | Accepted | 2026-05-06 |
| [0003](./0003-database-postgres-jsonb.md) | Use PostgreSQL with a JSONB-first schema for `Study` persistence | Accepted | 2026-05-06 |
| [0004](./0004-gemma4-12b-q4km.md) | Use Gemma 4 12B Q4_K_M for production extraction; 4B for CI/dev | Accepted | 2026-05-06 |
| [0005](./0005-extraction-accuracy-f1-metric.md) | Extraction Accuracy F1 metric | Accepted | 2026-05-10 |
| [0006](./0006-message-broker-rabbitmq.md) | Message Broker for Asynchronous LLM Evaluation (RabbitMQ) | Accepted | 2026-06-24 |
| [0007](./0007-infra-orchestration-docker-compose.md) | Orchestrate infrastructure (PostgreSQL, RabbitMQ, Ollama) with Docker Compose | Accepted | 2026-06-26 |
| [0008](./0008-dependency-management-uv.md) | Adopt uv for dependency management; retire Poetry and requirements.txt | Accepted | 2026-06-26 |

## When to write a new ADR

Write an ADR when **any** of the following is true:

* The decision affects more than one module or layer.
* Reversing it would cost more than one day of work.
* You can imagine a future contributor litigating the choice without context.
* You chose between named alternatives and the runner-up was viable.

ADRs are **append-only**: once accepted, do not edit; supersede with a new ADR that references the old one.

## Rejected by convention (don't re-litigate without a new ADR)

* Streamlit / Gradio for the frontend → see [ADR-0001](./0001-architecture-hexagonal.md) and [`FitSci - Stack Analysis.md`](../stack/FitSci%20-%20Stack%20Analysis.md).
* LangChain / LlamaIndex for orchestration → simple prompt-chaining inside `adapters/ai/` until a workload demonstrably needs a framework.
* MongoDB / SQLite as primary storage → see [ADR-0003](./0003-database-postgres-jsonb.md).
* RAG / vector search in v1 → see [`audit-database.md §6`](../audit/before-phase-0/audit-database.md).
* Closed-weights frontier models for extraction → violates the Gemma 4 Good hackathon brief; see [ADR-0004](./0004-gemma4-12b-q4km.md).

---

*Companion documents: [`FitSci - Development Plan.md`](../architecture/FitSci%20-%20Development%20Plan.md) · [`FitSci - Technical Architecture.md`](../architecture/FitSci%20-%20Technical%20Architecture.md).*
