# FitSci Evaluator — Evidence-Based Fitness AI

> **A bridge between complex science and gym practice.** An intelligent system that uses **Google Gemma 4** to extract structured methodology data from sport-science publications and applies a **deterministic Rigor Index** to deliver a transparent **Credibility Verdict**.
>
> *Project for the Kaggle hackathon: Gemma for Good.*

---

## Quick links

* **Start here:** [docs/INDEX.md](./docs/INDEX.md) — full navigation map for every document in the repo.
* **Master plan:** [docs/FitSci - Development Plan.md](./docs/FitSci%20-%20Development%20Plan.md) — phases, measurable DoDs, time-boxes, risks.
* **Architecture:** [docs/FitSci - Technical Architecture.md](./docs/FitSci%20-%20Technical%20Architecture.md) · [docs/FitSci - Directory Structure.md](./docs/FitSci%20-%20Directory%20Structure.md) · [docs/adr/](./docs/adr/README.md).
* **Scoring spec (v1, what runs):** [docs/scoring_basis.md](./docs/scoring_basis.md).
* **Audit reports (post-implementation review):** [docs/internal/audit/](./docs/internal/audit/audit-index.md).

---

## 1. The Problem

The fitness industry runs on misinformation. Sensational headlines appear daily — *"new study: this supplement increases muscle mass by 50%!"* — and most people training have neither the time nor the methodological literacy to verify them.

Concrete failure modes:

* **Interpretational errors.** Drawing conclusions from *noob-gain* studies that don't generalize to advanced trainees.
* **Statistical illiteracy.** Conflating *p-value* with *effect size*, ignoring sample size and heterogeneity.
* **Information noise.** Changing training plans every week based on isolated, low-quality reports.

## 2. The Solution

**FitSci Evaluator** acts as a personal scientific reviewer. Given a PMCID (or a paper text), it:

1. **Fetches** the paper (Ingestor / `IngestorPort`).
2. **Extracts** a 30+-field structured `Study` JSON via Gemma 4 (Sifter / `EvaluatorPort`).
3. **Scores** the study with a deterministic Rigor Index in pure Python (Judge / `ScoringService`).
4. **Persists** the evaluation (Vault / `RepositoryPort`).
5. **Renders** a Credibility Verdict — score, quality tier, confidence, breakdown, summaries.

The Judge is **deterministic**. Gemma extracts; it never scores.

## 3. Architecture (Hexagonal — Ports & Adapters)

The codebase is organized into a pure **domain core**, a thin **application** orchestration layer, and **adapters** for every external system. Decision recorded in [ADR-0001](./docs/adr/0001-architecture-hexagonal.md); full layout in [docs/FitSci - Directory Structure.md](./docs/FitSci%20-%20Directory%20Structure.md).

* `backend/src/domain/` — Pydantic models (`Study`, `Population`, `Delta`, `Dosage`, `ScoreBreakdown`, `StudyFlags`), pure services (`ScoringService`), and `typing.Protocol` ports (`IngestorPort`, `EvaluatorPort`, `RepositoryPort`, `LoggerPort`, `ClockPort`).
* `backend/src/application/use_cases/` — orchestrators (Phase 0: `EvaluateStudyUseCase` skeleton; Phase 1+ fills the workflow and adds read use cases).
* `backend/src/adapters/` — the **only** modules permitted to import third-party SDKs: `ai/` (Gemma via Ollama / Vertex AI), `scrapers/` (PMC, PDF), `db/` (Postgres / in-memory), `api/` (FastAPI), `logging/`, `clock/`, `cache/`.
* `backend/src/cli/` and `backend/src/main.py` — composition roots.

## 4. Scoring (v1 — what runs today)

Documented in [docs/scoring_basis.md](./docs/scoring_basis.md). Bounded **Rigor Index 0–14** with deterministic `confidence` (0–100). Quality tiers: `high` (≥8) · `moderate` (5–7) · `rejected` (<5).

The **v2 conceptual model** (0–20, MRI-vs-DEXA, Cohen's d–first) is documented in [docs/FitSci - Research Evaluation Model.md](./docs/FitSci%20-%20Research%20Evaluation%20Model.md) as the long-term science target. Migration is gated on extraction accuracy proven in Phase 1; see [ADR-0002](./docs/adr/0002-scoring-canonical-spec.md).

## 5. Roadmap (summary)

The full plan with measurable Definitions of Done, time-boxes, cross-cutting concerns, and risks is in [docs/FitSci - Development Plan.md](./docs/FitSci%20-%20Development%20Plan.md). At a glance:

| Phase | Goal | Status | Budget |
|---|---|---|---|
| **0 — Foundation** | ADRs, error taxonomy, `LoggerPort`/`ClockPort`, application layer skeleton, CI bootstrap | ✅ done | 1 day |
| **1 — Core Scientist (CLI)** | Real Ingestor + real Gemma + Judge end-to-end on 5 benchmark PMCIDs; **no mock data** | 🚧 in progress (`PMCAdapter` implemented) | 3 days |
| **2 — Bridge (FastAPI)** | Versioned `/api/v1/`, idempotent `POST /evaluate` with job IDs, Postgres + Alembic, OpenAPI snapshot | ⏳ | 2 days |
| **Schema-freeze gate** | `Study` model becomes immutable v1 contract | ⏳ | — |
| **3 — Bio-Signal Dashboard** | React migration onto codegen'd typed client; visual parity with legacy app | ⏳ | 2 days |
| **4 — Fine-tuning + features** | QLoRA on Gemma 4 12B + 6 feature extensions (lay translator, p-hack sniffer, comparator, myth-buster, citation triage, co-pilot) | 📦 deferred | 2–4 weeks |

## 6. Local usage

### Prerequisites

* Python 3.11+
* (Phase 1+) [Ollama](https://ollama.com/) running locally with `gemma4:12b-q4_k_m` (or `:4b-q4_k_m` on weak hardware)
* (Phase 2+) Docker (for PostgreSQL via testcontainers) **or** a local PostgreSQL 16+ instance

### Run the existing CLI (mock-data MVP)

From the `backend` directory:

```bash
pip install -r requirements.txt
python -m pytest
python -m src.cli.main PMC12345
```

### Console script

```bash
pip install -e .
fitsci-evaluate PMC12345
```

Or with Poetry:

```bash
poetry install
fitsci-evaluate PMC12345
```

> **Note (current state):** the CLI still uses hardcoded mock data. Phase 1 progress: `PMCAdapter` is implemented (NCBI E-utilities + local raw-byte cache + tests), while `GemmaOllamaAdapter` and use-case/CLI wiring are still pending.

## 7. Stack (locked — see [docs/adr/](./docs/adr/README.md))

| Layer | Choice | ADR |
|---|---|---|
| Architecture | Hexagonal (Ports & Adapters) | [ADR-0001](./docs/adr/0001-architecture-hexagonal.md) |
| Backend | Python 3.11+ / FastAPI / Pydantic v2 | [ADR-0001](./docs/adr/0001-architecture-hexagonal.md) |
| Frontend | React (Vite + TypeScript) — Bio-Signal aesthetic | — |
| LLM (production extraction) | Gemma 4 12B Q4_K_M via Ollama / Vertex AI | [ADR-0004](./docs/adr/0004-gemma4-12b-q4km.md) |
| LLM (CI / dev / lightweight features) | Gemma 4 4B Q4_K_M via Ollama | [ADR-0004](./docs/adr/0004-gemma4-12b-q4km.md) |
| Database | PostgreSQL 16+ with JSONB-first schema | [ADR-0003](./docs/adr/0003-database-postgres-jsonb.md) |
| Migrations | Alembic | — |
| API contract | OpenAPI 3 → `openapi-typescript` codegen | — |

> **Out of scope for v1:** Retrieval-Augmented Generation, vector search, multi-tenant authentication, real-time streaming. The system *evaluates* papers; it does not retrieve from them.

## 8. Target audience

* **Physique sports amateurs** — train smarter, not harder.
* **Personal trainers** — quick knowledge verification + client education.
* **Content creators** — build authority on reliable evidence (Evidence-Based).

## 9. Contributing

1. **Read the docs first.** Start at [docs/INDEX.md](./docs/INDEX.md). Skim the audits in [docs/internal/audit/](./docs/internal/audit/audit-index.md) before opening a non-trivial PR.
2. **Domain stays pure.** No third-party imports inside `backend/src/domain/` (Pydantic is the deliberate exception).
3. **Adapter discipline.** Wrap third-party exceptions into the `domain/errors.py` taxonomy; never leak SDK types upward.
4. **Tests are not optional.** Every PR adds tests for any changed behavior. CI enforces coverage thresholds.
5. **Scoring spec consistency.** Any change to `backend/src/domain/services/scoring.py` requires a touched `docs/scoring_basis.md` in the same commit ([ADR-0002](./docs/adr/0002-scoring-canonical-spec.md)).
6. **One port per responsibility.** New use case → new port → new adapter. Never widen `EvaluatorPort` to absorb new tasks.

## 10. License

See [LICENSE](./LICENSE).

---

*Companion documents: [docs/INDEX.md](./docs/INDEX.md) · [docs/FitSci - Development Plan.md](./docs/FitSci%20-%20Development%20Plan.md) · [docs/FitSci - Risk Register.md](./docs/FitSci%20-%20Risk%20Register.md) · [docs/FitSci - Cross-Cutting Concerns.md](./docs/FitSci%20-%20Cross-Cutting%20Concerns.md).*
