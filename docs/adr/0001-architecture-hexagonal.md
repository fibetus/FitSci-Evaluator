# ADR-0001 — Adopt Hexagonal (Ports & Adapters) Architecture

* **Status:** Accepted
* **Date:** 2026-05-06
* **Decision drivers:** scientific-rigor ethos (deterministic Judge), Gemma model swappability, future fine-tuning track, CLI-to-UI development order.
* **Related:** [`FitSci - Technical Architecture.md`](../FitSci%20-%20Technical%20Architecture.md), [`audit-architecture.md`](../audit/before-phase-0/audit-architecture.md).

## Context

FitSci - Evaluator must:

1. Run a **deterministic** scoring engine over Gemma-extracted study metadata. The Judge is the project's defensibility — it cannot live behind an LLM.
2. **Swap LLM providers** without code changes inside the scoring rules: dev runs Gemma 4 via Ollama, production runs Gemma 4 via Vertex AI, Phase 4 introduces a fine-tuned Gemma adapter behind a routing layer ([`audit-finetuning-pipeline.md §4`](../audit/before-phase-0/audit-finetuning-pipeline.md)).
3. Develop **inside-out (CLI → API → UI)** so the science core ships before any web surface is wired.
4. Survive a frontend migration from a legacy React MVP onto a typed, codegen'd contract.

## Decision

Adopt **Option A — Hexagonal (Ports & Adapters)** as defined in [`FitSci - Technical Architecture.md §1`](../FitSci%20-%20Technical%20Architecture.md):

* `domain/` is pure: stdlib + Pydantic only.
* `domain/ports/` defines `typing.Protocol` interfaces (structural typing).
* `adapters/` is the **only** place permitted to import third-party SDKs (`httpx`, `asyncpg`, `ollama`, `google.cloud.aiplatform`, ...).
* `application/use_cases/` orchestrates ports for one user-facing operation (the missing layer flagged in [`audit-architecture.md §3`](../audit/before-phase-0/audit-architecture.md)).
* `cli/main.py` and `main.py` (FastAPI) are the only **composition roots** — they construct adapters and inject them into use cases.

### Pydantic exception
Pydantic is **explicitly permitted in `domain/`** as a domain-validation library, not as infrastructure. This is a deliberate trade-off: rewriting field validation by hand would cost more than the (negligible) coupling benefit. Documented in [`FitSci - Directory Structure.md §2`](../FitSci%20-%20Directory%20Structure.md).

## Alternatives considered

* **Option B — Clean Layered (`API → Service → Repository`).**
  Pro: faster to build; familiar.
  Con: layers couple over time; SDK types leak into service code; the "5-line LLM swap" promise becomes a refactor.
  Rejected because the project's headline differentiator (provider-agnostic Judge) requires stronger interface hygiene than layered conventionally provides.

* **Option C — Modular Monolith (Command/Event communication).**
  Pro: extreme isolation; easy future extraction to microservices.
  Con: ceremony cost (Command/Event objects, serializers, dispatcher) is too high for a one- or two-person team building a hackathon-scale codebase.
  Rejected as overkill at current scale.

## Consequences

### Positive
* **Deterministic Judge stays pure.** `domain/services/scoring.py` cannot accidentally call an LLM.
* **LLM swap is a constructor-arg change.** Confirmed by [ADR-0004](./0004-gemma4-12b-q4km.md) routing.
* **Tests run without infrastructure.** Every domain test uses an `InMemoryStudyRepository`; integration tests opt into real Postgres / Ollama.
* **Phase 4 fine-tuning track is unblocked.** A fine-tuned `EvaluatorPort` adapter slots in behind a routing adapter; no domain change required.
* **Frontend isolation.** UI is a sibling consumer of the JSON contract; never imports backend types directly.

### Negative
* **Higher initial scaffolding cost.** Phase 0 exists specifically to pay this — `application/use_cases/`, `domain/errors.py`, `LoggerPort`, `ClockPort`.
* **Discipline required.** Adapter authors must wrap third-party exceptions into the [`domain/errors.py`](../FitSci%20-%20Cross-Cutting%20Concerns.md) taxonomy; this is enforced by code review and by integration tests.

### Neutral
* `Study` is anemic (data + Pydantic validators only); behavior lives in `ScoringService`. This is the canonical "anemic domain model" pattern. We accept it as Pythonic and consistent with the rest of the LLM-pipeline ecosystem.

## Compliance check

* CI `mypy --strict` on `backend/src` catches accidental third-party imports inside `domain/` (e.g. `from sqlalchemy import`).
* `tests/unit/test_imports.py` AST-guards that `domain/` modules only import Pydantic, stdlib, or other `domain/` packages.

---

*Superseded by:* (none yet)
