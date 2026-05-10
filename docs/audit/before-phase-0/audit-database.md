# Audit — Database Selection

**Date:** 2026-05-02
**Last reviewed by:** Claude Opus (automated audit)
**TL;DR:** Keep **PostgreSQL** as planned, but configure it deliberately as a **JSONB-first document store with a thin relational shell**, not as a fully normalized relational DB. The `Study` model is one large, document-shaped aggregate with optional fields and nested objects — it is fundamentally a document, not a table. PostgreSQL with JSONB gives the document ergonomics of MongoDB, ACID guarantees, full-text search, and a future on-ramp to `pgvector` if you ever add semantic search over evaluations or papers — all behind a single `RepositoryPort`.

---

## 1. Recommendation

**Primary: PostgreSQL 16+ with JSONB columns, accessed via SQLModel through a `PostgresStudyRepository` adapter.**

### Justification (5 sentences)
1. The `Study` aggregate has 30+ fields, four nested objects (`Population`, `Delta`, `Dosage`, `ScoreBreakdown`), several optional `Literal` enums, and an open `flags: dict` — this is a **document shape**, and forcing it into 6+ relational tables creates impedance mismatch with no payoff because there are no cross-aggregate joins planned in the docs.
2. Read patterns described in `Development Plan §4.2` are simple — `GET /studies` (list), `GET /studies/{id}` (by-ID), and at most filtering by `topic`/`quality_tier` — none of which require relational joins; all are first-class indexable JSONB queries.
3. Write patterns are very low volume (one row per `POST /evaluate`, expected at most a few hundred to a few thousand evaluations) so OLTP performance is a non-issue; the choice is dictated by *schema flexibility* and *operational simplicity*.
4. The "Extract & Discard" pattern explicitly stated in `Development Plan §M4` (raw paper text is *not* persisted, only the evaluation JSON) means the DB is essentially a write-once, read-many evaluation log — exactly the workload JSONB excels at.
5. PostgreSQL ships with **GIN indexes on JSONB**, **`tsvector` full-text search** for the multilingual summary fields (`summary_pl`, `summary_en`), and **`pgvector`** as a single-extension upgrade path if Phase 4+ adds semantic search over evaluations — no migration required.

### Concrete schema sketch
```sql
CREATE TABLE studies (
    id              TEXT PRIMARY KEY,             -- PMCID
    pmid            TEXT,
    doi             TEXT,
    topic           TEXT NOT NULL,                -- promoted for cheap filtering
    quality_tier    TEXT NOT NULL,                -- promoted for cheap filtering
    score           INT  NOT NULL,
    confidence      INT  NOT NULL,
    year            INT  NOT NULL,
    document        JSONB NOT NULL,               -- full Study Pydantic model
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_studies_topic        ON studies (topic);
CREATE INDEX idx_studies_quality_tier ON studies (quality_tier);
CREATE INDEX idx_studies_score        ON studies (score);
CREATE INDEX idx_studies_document_gin ON studies USING GIN (document jsonb_path_ops);
```

The promoted columns (`topic`, `quality_tier`, `score`, `year`) are denormalized from the JSONB document for fast list/filter queries. The full `Study` is reconstructed from `document` on read.

---

## 2. Rationale Comparison Table

| Attribute | **PostgreSQL + JSONB (chosen)** | SQLite + JSON1 | MongoDB | Fully-normalized PostgreSQL |
|---|---|---|---|---|
| **Schema flexibility for `Study` document shape** | ✅ Native JSONB | ✅ JSON1 | ✅ Native | ❌ 6+ tables, joins on every read |
| **Hexagonal swappability (back behind `RepositoryPort`)** | ✅ Trivial | ✅ Trivial | ✅ Trivial | ✅ but more painful (more SQL surface) |
| **Local dev simplicity** | ⚠️ Needs Docker or local install | ✅ Single file | ⚠️ Docker | ⚠️ Same as JSONB |
| **Full-text search (Polish + English)** | ✅ `tsvector` with `polish` + `english` configs | ⚠️ FTS5 (English-biased) | ✅ Atlas Search (cloud only) | ✅ Same |
| **Vector search future-proofing (pgvector)** | ✅ One extension | ❌ None | ⚠️ Atlas Vector (cloud only) | ✅ Same |
| **Migrations / schema evolution** | ✅ Alembic | ✅ Alembic | ⚠️ Schema-less = silent drift | ✅ Alembic |
| **Operational simplicity (hackathon)** | ⚠️ Medium | ✅ Highest | ⚠️ Medium | ⚠️ Medium |
| **ACID across concurrent writes** | ✅ | ⚠️ writer-locks | ✅ (single doc) | ✅ |
| **Query power for nested filters** | ✅ JSONB path ops | ⚠️ JSON1 limited | ✅ | ✅ |
| **Match to `Study` aggregate boundary** | ✅ One row = one aggregate | ✅ Same | ✅ Same | ❌ Aggregate split across tables |

---

## 3. Alternative Recommendation: SQLite + JSON1 (for hackathon scope only)

**When to choose SQLite instead:** if the hackathon timebox is tight (<5 days), if there is no Docker available on the target demo machine, or if the project will never run multi-process.

### Trade-offs
| | SQLite | PostgreSQL |
|---|---|---|
| Setup time to first migration | ~5 min | ~30 min (Docker, env vars, connection string, healthcheck) |
| Multilingual full-text search | Weak | Strong (Polish stemming via `polish.stop` config) |
| Multi-process / async concurrent writes | Limited (SQLite locks the whole DB) | Native MVCC |
| Vector search upgrade path | Forces a rewrite | One `CREATE EXTENSION pgvector;` |
| What `RepositoryPort` looks like | Identical | Identical |

**Verdict:** If the team is uncomfortable with Docker for the hackathon demo, ship the MVP on SQLite, ensure the `RepositoryPort` is the *only* DB surface, and migrate to PostgreSQL post-hackathon. **The whole point of the hexagonal design is that this swap is a 1-day task, not a refactor.**

---

## 4. Repository Port Design (Implementation Recipe)

### 4.1 The port (already exists, audit OK)
The current `domain/ports/repository.py` is good but minimal:
```python
class RepositoryPort(Protocol):
    async def save(self, study: Study) -> None: ...
    async def get_by_id(self, study_id: str) -> Optional[Study]: ...
    async def list_all(self, topic: Optional[str] = None) -> List[Study]: ...
```
**Recommended additions** (still pure Python, no infra):
```python
class RepositoryPort(Protocol):
    async def save(self, study: Study) -> None: ...
    async def get_by_id(self, study_id: str) -> Optional[Study]: ...
    async def list_by(
        self,
        topic: Optional[StudyTopic] = None,
        quality_tier: Optional[QualityTier] = None,
        min_score: Optional[int] = None,
        year_from: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Study]: ...
    async def exists(self, study_id: str) -> bool: ...
    async def delete(self, study_id: str) -> None: ...
```
Pagination + structured filters are essential for the React Bio-Signal grid, which paginates through study cards.

### 4.2 Adapter contract (PostgreSQL)
```text
backend/src/adapters/db/postgres_study_repository.py
    class PostgresStudyRepository(RepositoryPort):
        def __init__(self, session_factory): ...
        async def save(self, study): 
            # serialize Study → dict via study.model_dump(mode="json")
            # UPSERT into studies (id, ..., document) ON CONFLICT (id) DO UPDATE
        async def get_by_id(self, study_id):
            # SELECT document FROM studies WHERE id = $1
            # return Study.model_validate(row.document) if row else None
        async def list_by(...):
            # build parameterized SQL using only the promoted columns
            # rebuild Study objects from document JSONB
```
The adapter **re-hydrates `Study` objects via `Study.model_validate(row.document)`**, so the domain never sees a raw row, a SQLAlchemy entity, or a column. The DB is invisible.

### 4.3 In-memory adapter for tests
```text
backend/src/adapters/db/in_memory_repository.py
    class InMemoryStudyRepository(RepositoryPort):
        def __init__(self): self._store: dict[str, Study] = {}
        async def save(self, study): self._store[study.id] = study.model_copy(deep=True)
        ...
```
Every domain test and use-case test should use this. Database adapters get *integration* tests against a real PostgreSQL instance (or testcontainers), nothing more.

### 4.4 DI wiring
- `cli/main.py` constructs `InMemoryStudyRepository` (or `PostgresStudyRepository` if a `--db` flag is passed).
- `main.py` (FastAPI) constructs `PostgresStudyRepository` from a config-loaded session factory and injects it via FastAPI `Depends()`.
- The use-case layer (recommended in architecture audit §4.2) accepts the port via constructor — never imports the adapter directly.

---

## 5. Anti-patterns to Avoid

| ⛔ Don't | Why it breaks hexagonal swappability |
|---|---|
| Import `sqlmodel`, `sqlalchemy`, `psycopg`, `asyncpg`, or any DB driver from anywhere inside `domain/` | Couples the domain to PostgreSQL forever. |
| Make `Study` inherit from `SQLModel` | This is the textbook trap — `SQLModel` blends Pydantic and SQLAlchemy, and "domain that is also an ORM entity" is the canonical leak. Keep `Study` as **pure `BaseModel`** and have a separate `StudyRow` table model inside `adapters/db/`. |
| Leak `AsyncSession` into the use-case or domain | Sessions are an infrastructure concept. The repository owns them. |
| Use auto-incrementing integer IDs | The natural key is the PMCID (`PMC12345`). Using surrogate integer IDs forces double-lookup logic and breaks idempotency on `POST /evaluate`. |
| Store the original raw paper text in PostgreSQL | Violates the "Extract & Discard" pattern stated in `Development Plan §M4`. If you ever need raw text, store it in object storage (S3-compatible) referenced by URL, not in the JSONB. |
| Add a `score_breakdown` column separate from `document` | Causes write-time inconsistency between the flat columns and the JSONB. Promoted columns must be **read-derived projections**, written by the same `save()` call from the same `Study` object. |
| Use Mongo because the data is "document-shaped" | You give up ACID, multilingual FTS, mature Alembic-style migrations, and `pgvector` for zero practical benefit at this scale. |
| Bypass the port from FastAPI (e.g. injecting `AsyncSession` directly into a route) | The route becomes infrastructure-coupled and the API can no longer be tested without a real DB. |
| Run migrations from inside application code (e.g. `Base.metadata.create_all()` at startup) | Hides schema state. Use Alembic with a versioned migration file per change, run as a separate command. |

---

## 6. ⛔ BLOCKER (informational): vector search is not in scope yet
`README.md` line 56 mentions "RAG (Retrieval-Augmented Generation)" but no other `/docs` file references vector search, embedding storage, or semantic retrieval. Either:
- (a) Confirm RAG is **out of scope for v1** (most likely — the project is *evaluating* papers, not retrieving from them), and remove the README line; OR
- (b) Add a Phase 4 design note for `pgvector` integration with a `VectorRepositoryPort`.

This decision affects nothing immediately, but the README's mention should not survive untouched.

---

*End of database audit.*
