# 03 — Architectural Integrity

This file audits the actual repository against the hexagonal-architecture rules stated in `docs/adr/0001-architecture-hexagonal.md`, `docs/FitSci - Directory Structure.md §2`, and `docs/FitSci - Development Plan.md §7`.

---

## 4.1 — Dependency rule (the cardinal rule)

**Rule:** `domain/` may import only stdlib, `pydantic`, or other `domain/` modules.

**Verdict:** `✅`

Every import in every `domain/` file:

| File | Imports |
|---|---|
| `backend/src/domain/__init__.py` | (empty) |
| `backend/src/domain/errors.py` | (no imports) |
| `backend/src/domain/models/__init__.py` | (empty) |
| `backend/src/domain/models/study.py:1-4` | `datetime`, `typing`, `pydantic` |
| `backend/src/domain/ports/__init__.py` | (empty) |
| `backend/src/domain/ports/clock.py:1-2` | `datetime`, `typing.Protocol` |
| `backend/src/domain/ports/evaluator.py:1,3` | `typing.Protocol`, `..models.study.Study` |
| `backend/src/domain/ports/ingestor.py:1` | `typing.List, Protocol` |
| `backend/src/domain/ports/logger.py:1` | `typing.Any, Protocol` |
| `backend/src/domain/ports/repository.py:1,3` | `typing.Protocol`, `..models.study.{QualityTier, Study, StudyTopic}` |
| `backend/src/domain/services/__init__.py` | (empty) |
| `backend/src/domain/services/scoring.py:1,3` | `pydantic.{BaseModel, ConfigDict}`, `..models.study.{QualityTier, ScoreBreakdown, Study}` |

**Zero violations.** No `httpx`, no `sqlalchemy`, no `ollama`, no `fastapi`, no `random`, no `os`, no I/O. The dependency rule is honored.

---

## 4.2 — Port completeness

**Rule:** every method declared in a Protocol is implemented in every non-test adapter; ports use `typing.Protocol` (not `abc.ABC`); no port has a silent default implementation.

### Existing ports — implementations exist

| Port | Methods declared | Adapter | Methods implemented |
|---|---|---|---|
| `IngestorPort` (`ingestor.py:4`) | `fetch_by_id`, `search` | `PMCAdapter` (`pmc.py:13`) | ✅ both (`pmc.py:32`, `pmc.py:68`) |
| `EvaluatorPort` (`evaluator.py:6`) | `evaluate_text` | `GemmaOllamaAdapter` (`gemma_ollama.py:14`) | ✅ (`gemma_ollama.py:54`) |
| `RepositoryPort` (`repository.py:6`) | `save`, `get_by_id`, `list_by`, `exists`, `delete` | `InMemoryStudyRepository` (`in_memory_repository.py:7`) | ✅ all five (`in_memory_repository.py:11, 14, 17, 43, 46`) |
| `LoggerPort` (`logger.py:4`) | `info`, `warning`, `error`, `with_context` | `ConsoleLogger` (`logger.py:8`, adapter file) | ✅ all four (`logger.py:12, 15, 18, 23`) |
| `ClockPort` (`clock.py:5`) | `now` | `SystemClock` (`clock.py:6`, adapter file) | ✅ (`clock.py:7`) |

All five existing ports use `typing.Protocol`. None declares a method body other than `...` — i.e. none has a default-implementation footgun.

### Missing ports prescribed by the Plan and CCC

| Port | Required by | Status |
|---|---|---|
| `CachePort` | `docs/FitSci - Cross-Cutting Concerns.md §4` lines 137–143; Plan line 144 | ⛔ `domain/ports/cache.py` does not exist |
| `MetricsPort` | `docs/FitSci - Cross-Cutting Concerns.md §5` lines 162–172; Plan line 144 | ⛔ `domain/ports/metrics.py` does not exist |

`docs/FitSci - Directory Structure.md` lines 22–23 even has these two ports listed in the target tree with `⏳ Phase 1` markers. Phase 1 is marked complete; the ports are not.

**Verdict:** `⚠️ Partial`. Existing ports are sound; required ports are missing.

---

## 4.3 — Application layer rule

**Rule (Plan §3 M5 line 80):** "CLI and FastAPI controllers call use cases, never the domain directly."

**Verdict:** `⚠️ Partial`

* **Real path (lines 51–74 of `backend/src/cli/main.py`):** ✅ Constructs adapters, builds `EvaluateStudyUseCase`, calls `use_case.execute(args.id)`. No direct domain calls.
* **`--mock` path (lines 23–50):** ⛔ Constructs a `Study` object directly (line 25), then calls `ScoringService.calculate_rigor_index(mock_study)` directly at line 45. This is a CLI-to-domain call that bypasses the application layer.

The mock path is gated by `--mock`, but the rule wording in Plan §3 M5 is unconditional. Either move the mock data behind a `MockEvaluatorAdapter` and re-use the same `EvaluateStudyUseCase`, or reword the rule to allow flag-gated bypass paths.

`backend/src/main.py` (FastAPI controller, Phase 2) does not yet exist, so its compliance cannot be assessed.

---

## 4.4 — "The Judge is deterministic" — strategic principle #2

**Rule (Plan §1 line 18):** `ScoringService.calculate_rigor_index` accepts only its arguments, returns the same output for the same input, calls no port, imports no dynamic dependency.

**Verdict:** `✅` *for the Judge function itself.*

* `scoring.py:1-3` imports `pydantic` and `..models.study` — no `random`, no `datetime`, no `time`, no port.
* `scoring.py:19-148` reads only `study.*` attributes; it never calls any port, queries any clock, or generates any randomness.
* The function returns a frozen `ScoringResult` (`scoring.py:8-15`).

⚠️ **Adjacent finding (does not change the §4.4 verdict but is the same architectural concern at the next layer up):** the application layer mutates the `Study` object after scoring (`backend/src/application/use_cases/evaluate_study.py:49-53`). The Judge itself is pure, but the *aggregate that the rest of the system sees* is built by mutation. If a future contributor mistakes "the Judge is deterministic" for "Study objects in the system are immutable", the use-case behavior is misleading.

---

## 4.5 — "Extract & Discard" — strategic principle #6

**Rule (Plan §1 line 22):** "Raw paper bytes are never persisted. Only the structured `Study` JSON enters the database."

**Verdict:** `✅` *for the database boundary.*

* `Study` (`backend/src/domain/models/study.py:57-108`) has no `raw_text`, `xml_payload`, or equivalent field.
* `RepositoryPort.save` (`backend/src/domain/ports/repository.py:7`) takes only `Study` — the raw text returned by `IngestorPort.fetch_by_id` flows from the use case into the evaluator and then is dropped (`backend/src/application/use_cases/evaluate_study.py:31-44` — the local `raw_text` variable goes out of scope).

⚠️ **Adjacent observation (not a violation, but worth noting):** `PMCAdapter` writes raw NCBI XML to the local cache directory `~/.fitsci/cache/pmc/<PMCID>.xml` (`pmc.py:28, 59`). This is an *on-disk byte cache*, not the database, and is required by Plan §3 M1 line 52. The strategic principle says "never persisted *in the database*"; the on-disk cache is consistent with that interpretation. If the user reads the principle as "never written to durable storage of any kind", the cache is borderline. Either (a) tighten the docs to say "never persisted in the evaluation log / database", or (b) gate the on-disk cache behind an explicit retention policy.

---

## 4.6 — "One port, one responsibility"

**Rule (Plan §7 line 300):** "Never grow `EvaluatorPort.evaluate_text` into `evaluate_text_or_translate_or_summarize`."

**Verdict:** `✅`

| Port | Methods declared |
|---|---|
| `EvaluatorPort` | `evaluate_text` only (`evaluator.py:7`) |
| `IngestorPort` | `fetch_by_id`, `search` (`ingestor.py:5, 11`) — both ingestion-shaped |
| `RepositoryPort` | `save`, `get_by_id`, `list_by`, `exists`, `delete` — five CRUD-shaped methods, all on the same aggregate |
| `LoggerPort` | `info`, `warning`, `error`, `with_context` — four logger-shaped methods |
| `ClockPort` | `now` only |

No port has been widened beyond its single responsibility.

---

## 4.7 — DI over imports

**Rule (Plan §7 line 297):** "Adapters are constructed once at process start and injected into use cases."

**Verdict:** `✅`

* `backend/src/cli/main.py:53-66` is the single composition root for the CLI: it constructs `PMCAdapter`, `GemmaOllamaAdapter`, `InMemoryStudyRepository`, `ConsoleLogger`, `SystemClock` exactly once, then passes them as keyword arguments to `EvaluateStudyUseCase(...)`.
* `EvaluateStudyUseCase` is `@dataclass(frozen=True)` (`evaluate_study.py:12`): port references are stored on construction, not re-instantiated per call.
* `EvaluateStudyUseCase` does not import any concrete adapter (`grep "from src.adapters" backend/src/application` → 0 hits inside use cases).
* `ScoringService` is passed as a class type (`evaluate_study.py:19`) and called via `self.scorer.calculate_rigor_index(...)`. Static call — no instantiation.

The composition-root pattern is correctly applied. The only DI concern is that there is currently exactly one composition root (`cli/main.py`) — when the FastAPI entrypoint (`backend/src/main.py`) ships in Phase 2, the duplication of adapter construction must be refactored into a shared `composition.py` or equivalent to avoid drift between the two roots.

---

## Architectural integrity summary

| Section | Verdict |
|---|---|
| 4.1 Dependency rule | ✅ |
| 4.2 Port completeness (existing) | ✅ |
| 4.2 Port completeness (`CachePort`, `MetricsPort` missing) | ⚠️ Partial |
| 4.3 CLI calls use case (real path) | ✅ |
| 4.3 CLI calls use case (`--mock` path) | ⚠️ Partial |
| 4.4 Deterministic Judge | ✅ |
| 4.5 Extract & Discard at the DB boundary | ✅ |
| 4.6 One port, one responsibility | ✅ |
| 4.7 DI over imports | ✅ |

The hexagonal *skeleton* is healthy. The two material weaknesses are:
1. The two cross-cutting ports prescribed for Phase 1 (`CachePort`, `MetricsPort`) are missing entirely.
2. The `--mock` branch of the CLI is the only path in the codebase that calls the domain directly, gated by a flag rather than rewritten as a `MockEvaluatorAdapter`.

Neither weakness is a structural violation of the hexagonal pattern; both are correctible without touching `domain/`.
