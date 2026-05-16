# ADR-0003 — Use PostgreSQL with a JSONB-first schema for `Study` persistence

* **Status:** Accepted
* **Date:** 2026-05-06
* **Decision drivers:** the `Study` aggregate is document-shaped; multilingual (Polish + English) full-text search is required; future `pgvector` upgrade path is desirable; Phase 4 fine-tune requires durable evaluation logs.
* **Related:** [`audit-database.md`](../audit/before-phase-0/audit-database.md), [`FitSci - Directory Structure.md`](../FitSci%20-%20Directory%20Structure.md).

## Context

The `Study` aggregate (see `backend/src/domain/models/study.py`) has:

* **30+ fields** with several nested objects (`Population`, `Delta`, `Dosage`, `ScoreBreakdown`).
* **Optional `Literal` enums** (`StudyType`, `StudyTopic`, `QualityTier`, `LegalStatus`).
* **An open `flags` field** (Phase 0 will type this as `StudyFlags`).
* **Multilingual summary fields** (`summary_pl`, `summary_en`).

Read patterns are simple: list with filters by `topic`/`quality_tier`/`min_score`/`year`, and lookup by PMCID. Write patterns are very low volume (one row per evaluation; expected hundreds to low thousands of evaluations total). Per the Extract & Discard pattern, the database is essentially a write-once, read-many evaluation log.

## Decision

Use **PostgreSQL 16+ with a JSONB-first schema** behind a `RepositoryPort`. Do **not** normalize `Study` into 6+ relational tables. Promote a small set of columns from the JSONB document for cheap filtering.

### Schema sketch (full version in [`audit-database.md §1`](../audit/before-phase-0/audit-database.md))

```sql
CREATE TABLE studies (
    id              TEXT PRIMARY KEY,            -- PMCID
    pmid            TEXT,
    doi             TEXT,
    topic           TEXT NOT NULL,
    quality_tier    TEXT NOT NULL,
    score           INT  NOT NULL,
    confidence      INT  NOT NULL,
    year            INT  NOT NULL,
    document        JSONB NOT NULL,              -- full Study Pydantic model
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_studies_topic        ON studies (topic);
CREATE INDEX idx_studies_quality_tier ON studies (quality_tier);
CREATE INDEX idx_studies_score        ON studies (score);
CREATE INDEX idx_studies_document_gin ON studies USING GIN (document jsonb_path_ops);
```

### Adapter contract

`adapters/db/postgres_study_repository.py` implements `RepositoryPort` and re-hydrates `Study` via `Study.model_validate(row.document)`. The domain never sees a SQLAlchemy entity, a column name, or an `AsyncSession`. An in-memory adapter (`adapters/db/in_memory_repository.py`) is used by tests and by the CLI when the user passes `--in-memory`.

### Migrations

**Alembic.** Baseline migration (`alembic/versions/0001_initial.py`) is committed in Phase 2. Schema changes go through Alembic — never `Base.metadata.create_all()` at startup.

## Alternatives considered

| Alternative | Why considered | Why rejected |
|---|---|---|
| **Fully-normalized PostgreSQL** | Familiar relational style | 6+ tables for one document; joins on every read; aggregate split across tables — pure cost, no benefit at this scale |
| **SQLite + JSON1** | Single-file, no Docker | Weak Polish full-text; locks the whole DB on write; vector-search upgrade is a rewrite — fine for hackathon-only fallback but would not survive any concurrent demo |
| **MongoDB** | "The data is document-shaped" | Loses ACID across multiple ops, mature migrations, multilingual FTS, and `pgvector`; no practical benefit at this scale |
| **PostgreSQL + JSONB (chosen)** | Document ergonomics + ACID + FTS + `pgvector` upgrade path | — |

The full comparison table is in [`audit-database.md §2`](../audit/before-phase-0/audit-database.md).

## Consequences

### Positive
* **Schema flexibility.** New fields on the `Study` model land in the JSONB document with no migration; only promotion of new filter columns requires Alembic.
* **Multilingual FTS available.** `tsvector` with the `polish` and `english` configs are first-class (relevant for `summary_pl` / `summary_en`).
* **Vector search upgrade path.** `CREATE EXTENSION pgvector;` is a single command; a future `VectorRepositoryPort` slots into the same architecture without changing existing storage.
* **One row = one aggregate.** Matches the hexagonal `Study`-as-aggregate boundary.

### Negative
* **Local dev ceremony.** Requires Docker (or a local Postgres install) — heavier than SQLite. Mitigated by a dev-mode `InMemoryStudyRepository` adapter for quick CLI iteration; Postgres only required for Phase 2+.
* **Promoted-column duplication.** `topic`, `quality_tier`, `score`, `year` exist both in the JSONB document and as flat columns. The repository writes both atomically; no inconsistency is allowed (test in `tests/integration/test_repository_roundtrip.py`).

### Neutral
* If the project is later forced onto a single-binary deployment (no Docker), the hexagonal port absorbs the swap to SQLite — that is the explicit fallback plan in [`audit-database.md §3`](../audit/before-phase-0/audit-database.md).

## Anti-patterns to avoid (from [`audit-database.md §5`](../audit/before-phase-0/audit-database.md))

* Importing `sqlmodel`, `sqlalchemy`, or `asyncpg` from anywhere inside `domain/`.
* Making `Study` inherit from `SQLModel` (the canonical leak).
* Using auto-incrementing integer IDs (the natural key is the PMCID).
* Storing raw paper text in PostgreSQL (Extract & Discard).
* Bypassing the port from FastAPI (e.g. injecting `AsyncSession` directly into a route).
* Running migrations from inside application code.

---

*Superseded by:* (none yet)
