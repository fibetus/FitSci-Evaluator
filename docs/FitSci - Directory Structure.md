# FitSci - Hexagonal Project Structure

> **Status (2026-05-06):** target structure for the post-Phase-0 codebase. Items already implemented in `backend/src/` are marked ✅; items added during Phases 0–3 are marked 🚧 / ⏳. The CLI currently uses mock data; Phase 1 wires the real adapters.

The directory follows **Hexagonal Architecture** ([ADR-0001](./adr/0001-architecture-hexagonal.md)): pure domain core, ports as `typing.Protocol` interfaces, adapters as the **only** modules permitted to import infrastructure libraries (`httpx`, `asyncpg`, `sqlalchemy`, `ollama`, `google.cloud.aiplatform`, ...).

```text
fitsci-evaluator/
├── backend/                        # Python (FastAPI) backend
│   ├── src/
│   │   ├── domain/                 # CORE — pure Python (Pydantic-only third-party dep)
│   │   │   ├── models/             # ✅ Pydantic schemas (Study, Population, Delta, Dosage, ScoreBreakdown)
│   │   │   │   ├── study.py        # ✅
│   │   │   │   └── flags.py        # ⏳ StudyFlags Pydantic model (replaces Study.flags: dict)
│   │   │   ├── services/           # ✅ Pure domain services
│   │   │   │   └── scoring.py      # ✅ ScoringService (will become pure / non-mutating in Phase 0)
│   │   │   ├── ports/              # ✅ Protocols (no implementation)
│   │   │   │   ├── ingestor.py     # ✅
│   │   │   │   ├── evaluator.py    # ✅
│   │   │   │   ├── repository.py   # ✅ — extended with list_by(), exists(), delete() in Phase 0
│   │   │   │   ├── logger.py       # ⏳ LoggerPort (Phase 0)
│   │   │   │   ├── clock.py        # ⏳ ClockPort (Phase 0)
│   │   │   │   ├── cache.py        # ⏳ CachePort for LLM responses (Phase 1)
│   │   │   │   └── metrics.py      # ⏳ MetricsPort (Phase 1)
│   │   │   └── errors.py           # ⏳ Domain error taxonomy (Phase 0)
│   │   │
│   │   ├── application/            # ⏳ USE-CASES — orchestrate ports for one user-facing operation
│   │   │   └── use_cases/
│   │   │       ├── evaluate_study.py
│   │   │       ├── get_study.py
│   │   │       └── list_studies.py
│   │   │
│   │   ├── adapters/               # OUTBOUND/INBOUND — implementations of ports
│   │   │   ├── ai/
│   │   │   │   ├── gemma_ollama.py        # 🚧 Phase 1
│   │   │   │   ├── gemma_vertex.py        # ⏳ Phase 2 / production
│   │   │   │   ├── gemma_replay.py        # ⏳ CI / fixtures
│   │   │   │   ├── routing_evaluator.py   # 📦 Phase 4 (canary / A-B between base and fine-tuned)
│   │   │   │   └── prompts/               # versioned prompt templates
│   │   │   │       └── extract_v1.txt
│   │   │   ├── scrapers/
│   │   │   │   ├── pmc.py                 # 🚧 Phase 1 — PMC E-utilities
│   │   │   │   └── pdf.py                 # ⏳ Local PDF via PyMuPDF
│   │   │   ├── db/
│   │   │   │   ├── postgres_study_repository.py  # ⏳ Phase 2
│   │   │   │   └── in_memory_repository.py       # ⏳ Phase 0/1 — used by tests + CLI dev
│   │   │   ├── logging/
│   │   │   │   └── stdlib_logger.py       # ⏳ Phase 0 — adapts stdlib logging to LoggerPort
│   │   │   ├── clock/
│   │   │   │   └── system_clock.py        # ⏳ Phase 0
│   │   │   ├── cache/
│   │   │   │   └── in_memory_cache.py     # ⏳ Phase 1
│   │   │   ├── api/                       # ⏳ Phase 2 — FastAPI routers + DI
│   │   │   │   ├── routes/
│   │   │   │   │   ├── studies.py
│   │   │   │   │   ├── evaluate.py
│   │   │   │   │   ├── jobs.py
│   │   │   │   │   └── health.py
│   │   │   │   ├── deps.py                # FastAPI Depends() wiring
│   │   │   │   └── middleware.py          # request-ID, rate-limit, CORS
│   │   │   └── jobs/                      # ⏳ Phase 2 — async-job adapter (asyncio.Queue for now)
│   │   │       └── in_process_queue.py
│   │   │
│   │   ├── cli/                    # ✅ inbound CLI adapter
│   │   │   └── main.py             # ✅ — Phase 1 swaps mock data for real use case
│   │   │
│   │   └── main.py                 # ⏳ FastAPI entrypoint (Phase 2)
│   │
│   ├── tests/
│   │   ├── unit/                   # ✅ pure-domain tests; no adapters
│   │   ├── integration/            # ⏳ adapter tests (real PostgreSQL via testcontainers, real Ollama)
│   │   ├── benchmark/              # ⏳ Phase 1 — field-accuracy F1 vs gold fixtures
│   │   ├── contract/               # ⏳ Phase 2 — OpenAPI snapshot test
│   │   ├── security/               # ⏳ Phase 1 — prompt-injection probes
│   │   ├── e2e/                    # ⏳ Phase 3 — Playwright against running stack
│   │   └── fixtures/
│   │       └── benchmark/          # 🚧 Phase 1 — 5 hand-curated PMCID gold JSONs
│   │
│   ├── alembic/                    # ⏳ Phase 2
│   │   └── versions/
│   │       └── 0001_initial.py
│   ├── openapi/                    # ⏳ Phase 2 — committed snapshot of /openapi.json
│   │   └── v1.json
│   ├── .env.example                # ⏳ Phase 0
│   ├── pyproject.toml              # ✅
│   └── requirements.txt            # ✅
│
├── frontend/                       # React (Vite + TypeScript) — Bio-Signal UI
│   ├── src/
│   │   ├── api/
│   │   │   ├── types.ts            # ⏳ Phase 2/3 — generated by openapi-typescript
│   │   │   └── client.ts           # ⏳ Phase 3
│   │   └── ...                     # existing Bio-Signal components
│   ├── package.json
│   └── vite.config.ts
│
├── docs/                           # All product / engineering documentation
│   ├── INDEX.md                    # ⏳ Content table — start here
│   ├── FitSci - Evaluator context.md
│   ├── FitSci - Development Plan.md
│   ├── FitSci - Technical Architecture.md
│   ├── FitSci - Directory Structure.md          (this file)
│   ├── FitSci - Stack Analysis.md
│   ├── FitSci - Research Evaluation Model.md
│   ├── FitSci - Design.md
│   ├── FitSci - Cross-Cutting Concerns.md       # ⏳ Phase 0
│   ├── FitSci - Risk Register.md                # ⏳ Phase 0
│   ├── scoring_basis.md                         # ✅ canonical v1 scoring spec
│   ├── adr/                                     # ⏳ Phase 0 — Architecture Decision Records
│   │   ├── README.md
│   │   ├── 0001-architecture-hexagonal.md
│   │   ├── 0002-scoring-canonical-spec.md
│   │   ├── 0003-database-postgres-jsonb.md
│   │   └── 0004-gemma4-12b-q4km.md
│   └── internal/
│       ├── audit/                               # ✅ post-implementation audits
│       └── private/                             # ✅ source PDF + CLAUDE.md (gitignored content)
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # ⏳ Phase 0 — pytest + ruff + mypy --strict
│
├── .gitignore
├── LICENSE
└── README.md                       # entry point — points to docs/INDEX.md
```

---

## 1. How modularity works in this structure

* **Replacing Gemma 4.** Switch from `adapters/ai/gemma_ollama.py` to `adapters/ai/gemma_vertex.py`: change the constructor call in `main.py` (FastAPI DI) or `cli/main.py`. The domain never notices because it only depends on `EvaluatorPort`. See [ADR-0004](./adr/0004-gemma4-12b-q4km.md).
* **Replacing the database.** Same pattern: swap `PostgresStudyRepository` for `InMemoryStudyRepository` (tests) or a future `SqliteStudyRepository`. See [ADR-0003](./adr/0003-database-postgres-jsonb.md).
* **CLI-first development.** `backend/src/cli/main.py` constructs the same `EvaluateStudyUseCase` as the FastAPI controller. Anything that works in the CLI works in the API.
* **Direct-to-Gemma path.** A use case can construct `GemmaOllamaAdapter` and `ScoringService` directly without touching the scrapers — useful for `text-in / verdict-out` workflows.

---

## 2. Domain dependency rules

* `domain/` may import: stdlib, `pydantic`, other `domain/` modules.
* `domain/` may **not** import: anything else (no `httpx`, no `sqlalchemy`, no `ollama`, no `fastapi`).
* `application/` may import: `domain/`, stdlib, `pydantic`. Never adapters.
* `adapters/` may import: anything they need; this is where third-party SDKs live.
* `cli/` and `main.py` (FastAPI) may import everything — they are the composition roots.

The Pydantic-in-domain dependency is a deliberate exception (see [ADR-0001](./adr/0001-architecture-hexagonal.md)): Pydantic is acting as a domain-validation library, not as infrastructure.

---

## 3. Testing layout

| Test folder | Runs against | Frequency | Phase |
|---|---|---|---|
| `tests/unit/` | Pure domain — no adapters, no I/O | Every commit | 1+ |
| `tests/integration/` | Adapters (real PostgreSQL via testcontainers, real local Ollama) | Pre-merge + nightly | 2+ |
| `tests/benchmark/` | M2 extraction accuracy on 5 gold fixtures | Pre-merge if `adapters/ai/` changed | 1+ |
| `tests/contract/` | OpenAPI snapshot diff vs `openapi/v1.json` | Every commit | 2+ |
| `tests/security/` | Prompt-injection probes; refusal expectations | Pre-merge if `adapters/ai/prompts/` changed | 1+ |
| `tests/e2e/` | Playwright against full stack | Nightly | 3+ |

---

*Companion documents: [`FitSci - Technical Architecture.md`](./FitSci%20-%20Technical%20Architecture.md) · [`FitSci - Development Plan.md`](./FitSci%20-%20Development%20Plan.md) · [`adr/0001-architecture-hexagonal.md`](./adr/0001-architecture-hexagonal.md).*
