# 09 — Architectural Integrity Re-check (Post-Remediation)

> Performed: 2026-05-16, after the remediation tracked in [`08-remediation-progress.md`](./08-remediation-progress.md).
> **Follow-up:** R-12 … R-17 implemented 2026-05-16 — see [`10-architecture-hardening-progress.md`](./10-architecture-hardening-progress.md).
> Scope: verify the hexagonal contract from [ADR-0001](../../adr/0001-architecture-hexagonal.md), validate the "5-line LLM swap" promise from [ADR-0004](../../adr/0004-gemma4-12b-q4km.md), and re-baseline the findings in [`03-architectural-integrity.md`](./03-architectural-integrity.md).

---

## 1. Verdict at a glance

| Concern | Verdict | Δ vs `03-architectural-integrity.md` |
|---|---|---|
| Domain dependency rule (Pydantic + stdlib only) | ✅ Clean | Held |
| Application → adapters import (forbidden) | ✅ Clean | Held |
| Port completeness (`Cache`, `Metrics`, `Logger` in adapters) | ✅ Now present | ⛔ → ✅ |
| Deterministic Judge purity | ✅ Pure | Held |
| Use case mutates the aggregate | ✅ `model_copy` everywhere | ⚠️ → ✅ |
| Use case enforces `domain/errors.py` taxonomy | ✅ Wrapped via `try/except` ladder | ⛔ → ✅ |
| CLI bypasses use case | ✅ `--mock` now goes through use case | ⚠️ → ✅ |
| LLM-swap story ("5-line swap") | ⚠️ Real but heavier than claimed | New caveat |
| Port shape independence | ⚠️ `EvaluatorPort.evaluate_text -> Study` over-broad | New finding |
| Directory-structure doc ↔ reality drift | ⚠️ `adapters/logging` and `adapters/clock` paths still wrong | Held |

**Overall score: 9.2 / 10** (updated after R-12 … R-17 in [`10-architecture-hardening-progress.md`](./10-architecture-hardening-progress.md)). The hexagon is production-ready for Phase 2 scaffolding; remaining gap is optional `GemmaVertexAIAdapter` and FastAPI DI mirroring the CLI composition root.

---

## 2. Domain dependency rule

> Source: ADR-0001 §Decision; `FitSci - Directory Structure.md §2`.

Grep across `backend/src/domain/**` for non-permitted imports:

```text
backend/src/domain/models/study.py:    from pydantic import BaseModel, Field
backend/src/domain/services/scoring.py: from pydantic import BaseModel, ConfigDict
backend/src/domain/ports/*.py:          stdlib `typing` / `datetime` only
backend/src/domain/errors.py:           stdlib only
```

* No `httpx`, `sqlalchemy`, `ollama`, `fastapi`, or `logging` references in `domain/`.
* Pydantic is the only third-party import — covered by the explicit exception in ADR-0001 §Pydantic exception.

**Verdict: ✅ Clean.** Consider adding the optional `tests/unit/test_imports.py` AST guard mentioned in ADR-0001 §Compliance check; it would make this gate machine-enforced rather than reviewer-enforced.

---

## 3. Application-layer rule (`application/` may not import adapters)

`backend/src/application/use_cases/evaluate_study.py` imports:

```python
from src.domain.errors import ...
from src.domain.models.study import Study
from src.domain.ports.{clock, evaluator, ingestor, logger, metrics, repository} import ...Port
from src.domain.services.scoring import ScoringService
```

* No `from src.adapters...` anywhere under `backend/src/application/` (`rg "from src.adapters" backend/src/application` → 0 hits).
* Use case depends on Protocol ports (`*Port`) and on `ScoringService` (pure domain service, not a port). The direct dependency on `ScoringService` is intentional: scoring is internal domain logic, not an external boundary. ADR-0001 §Decision treats scoring this way.

**Verdict: ✅ Clean.** Minor nit: if v2 scoring is ever A/B-tested at runtime, `scorer: type[ScoringService]` will need to become a `ScorerPort` Protocol. Document that as a Phase 2.5 follow-up only.

---

## 4. Port inventory (Phase 1 contract surface)

| Port | File | Methods | Adapters wired today |
|---|---|---|---|
| `IngestorPort` | `domain/ports/ingestor.py` | `fetch_by_id`, `search` | `PMCAdapter`, `ReplayIngestorAdapter`, `MockIngestorAdapter` |
| `EvaluatorPort` | `domain/ports/evaluator.py` | `evaluate_text` | `GemmaOllamaAdapter`, `GemmaReplayAdapter`, `MockEvaluatorAdapter` |
| `RepositoryPort` | `domain/ports/repository.py` | `save`, `get_by_id`, `list_by`, `exists`, `delete` | `InMemoryStudyRepository` |
| `LoggerPort` | `domain/ports/logger.py` | `info`, `warning`, `error`, `with_context` | `ConsoleLogger`, `NullLogger` |
| `ClockPort` | `domain/ports/clock.py` | `now` | `SystemClock` |
| `CachePort` | `domain/ports/cache.py` | `get`, `set` | `InMemoryCache` |
| `MetricsPort` | `domain/ports/metrics.py` | `record_llm_call`, `record_evaluation` | `JsonlMetrics` |

All ports are `typing.Protocol` (structural typing), so concrete adapters don't need to inherit the Protocol — Pydantic-free, friction-free.

**Verdict: ✅ Complete for Phase 1.** All seven CCC ports exist and have at least one adapter; the closed `⛔` items from `03-architectural-integrity.md §4.1` are resolved.

---

## 5. Port independence (can adapters be swapped in isolation?)

### 5.1 `RepositoryPort` — ✅ Truly independent

`save(study) → None`, `get_by_id → Study | None`, `list_by(**domain_filters) → list[Study]`. The filter parameters use **domain Literals** (`StudyTopic`, `QualityTier`), not SQL or ORM types. A future `PostgresStudyRepository` only needs to translate filters to SQL and serialize `Study` to JSONB. Confirmed clean.

### 5.2 `IngestorPort` — ✅ Independent, with one caveat

Returns a plain `str`. PMC, PDF, and replay adapters can all conform. The plan-vs-code drift on `RawDocument` was resolved by editing the Plan (R-08 option b).

**Caveat:** the replay/mock ingestors smuggle metadata through a magic string `fitsci-pmc-id:PMCxxxx`. That's a test-fixture convenience, not a real architecture problem, but it does mean the **ingestor and replay-evaluator must agree on a side-channel**. Acceptable; document it in the replay adapter docstring (already done).

### 5.3 `EvaluatorPort` — ⚠️ Independent in principle, over-broad in practice

```python
class EvaluatorPort(Protocol):
    async def evaluate_text(self, text: str) -> Study: ...
```

Returning the full `Study` aggregate means every evaluator adapter must:

1. Know the 30+ schema fields, including **scoring fields** (`score`, `confidence`, `quality_tier`, `score_breakdown`) that the LLM should never set.
2. Supply reasonable defaults for `flags`, `population`, `dosage`, etc.

`GemmaReplayAdapter.evaluate_text` explicitly *strips* `score`, `confidence`, `quality_tier`, `score_breakdown`, `scraped_at` from the fixture before returning (`gemma_replay.py:34`). `EvaluateStudyUseCase.execute` then `model_copy(update={"score": ...})` *back in*. That round-trip is the contract telling you the type is wrong.

**Recommended refinement (R-12, not blocking Phase 2):**

```python
# domain/models/extraction.py
class ExtractionResult(BaseModel):
    # All Study fields *except* score, confidence, quality_tier, score_breakdown, scraped_at

# domain/ports/evaluator.py
class EvaluatorPort(Protocol):
    async def evaluate_text(self, text: str) -> ExtractionResult: ...
```

Then the use case composes `Study = ExtractionResult + ScoringResult + clock.now()`. This makes the deterministic-Judge invariant **type-level**: an LLM literally cannot return a score. Today it's enforced by `model_copy` discipline alone.

### 5.4 `CachePort` / `MetricsPort` — ⚠️ Wired inside `GemmaOllamaAdapter`

```python
class GemmaOllamaAdapter(EvaluatorPort):
    def __init__(self, ..., cache: CachePort | None = None, metrics: MetricsPort | None = None):
```

Every future evaluator adapter (`GemmaVertexAIAdapter`, `RoutingEvaluatorAdapter`, fine-tuned Gemma) must independently re-implement the cache/metrics plumbing, or the deployment loses caching.

**Recommended refinement (R-13, defer to Phase 2):**

```python
# adapters/ai/cached_evaluator.py
class CachedEvaluator(EvaluatorPort):
    def __init__(self, inner: EvaluatorPort, cache: CachePort): ...
    async def evaluate_text(self, text: str) -> Study:
        key = ...
        cached = await self.cache.get(key)
        if cached: return Study.model_validate_json(cached)
        result = await self.inner.evaluate_text(text)
        await self.cache.set(key, result.model_dump_json())
        return result
```

Same shape for `MeteredEvaluator`. The composition root then composes `MeteredEvaluator(CachedEvaluator(GemmaVertexAIAdapter(...)))`. This is the classic decorator pattern and makes the LLM swap genuinely orthogonal to cross-cutting concerns.

### 5.5 `LoggerPort` — ✅ Cleanly used

Adapters take `logger: LoggerPort | None = None` and default to `NullLogger`. Correlation IDs flow from CLI through `with_context`. Verified by `tests/integration/test_logging.py`.

**Small concern:** `NullLogger` lives in `adapters/system/null_logger.py` and is imported by `pmc.py`, `gemma_ollama.py`, `in_memory_repository.py`. This is an **adapter→adapter** import. Not architecturally wrong (both ends are in `adapters/`), but a no-op logger is conceptually a port-level default — moving it to `domain/ports/logger.py` (as `class NullLogger(LoggerPort): ...` next to the Protocol) removes the cross-adapter coupling.

---

## 6. LLM-swap claim verification

> ADR-0001 §Decision and ADR-0004 §Consequences both make a "5-line / constructor swap" promise.

### 6.1 Ollama → Vertex AI swap (today, with current code)

`backend/src/cli/main.py` line 37–41:

```python
evaluator = GemmaOllamaAdapter(
    logger=logger,
    cache=InMemoryCache(),
    metrics=metrics,
)
```

Swapping to a hypothetical `GemmaVertexAIAdapter` is **one constructor change** plus one import. The use case, the scoring service, the repository, and every test using `MockEvaluatorAdapter` / `GemmaReplayAdapter` are unaffected.

**Verified: ✅ Swap works.** But see §5.3–5.4 for the two refinements that would make the swap also automatically inherit cache + metrics.

### 6.2 Adding a fine-tuned variant (Phase 4 promise)

ADR-0004 §Phase 4 features promises a `RoutingEvaluatorAdapter` that A/Bs between base and fine-tuned models. Today's `EvaluatorPort` Protocol supports this with zero domain changes — the routing adapter is itself an `EvaluatorPort` implementation. Confirmed feasible.

### 6.3 CI / replay swap (already exercised)

`tests/integration/test_pipeline.py` runs the full pipeline with `GemmaReplayAdapter`. Production-vs-CI is already a runtime swap. Confirmed.

---

## 7. Deterministic-Judge invariant

`backend/src/domain/services/scoring.py` is a `@staticmethod` operating on the `Study` Pydantic model. No I/O, no clock, no randomness. Re-checked by `tests/test_scoring.py::test_determinism` (100 iterations identical) added in remediation B-04.

**Verdict: ✅ Pure.**

One subtle invariant gap (not a violation, a tightening opportunity): `EvaluatorPort.evaluate_text` *could* in principle return a `Study` with `score=12` and the use case would overwrite it. The deterministic Judge holds because the use case always re-scores, but a hostile evaluator implementation that *also* persisted a `Study` to its own backend could leak a non-deterministic score. Addressed by the §5.3 `ExtractionResult` refinement.

---

## 8. Composition root inspection (`backend/src/cli/main.py`)

```python
correlation_id = uuid.uuid4().hex
logger = ConsoleLogger(correlation_id=correlation_id)
clock = SystemClock()
metrics = JsonlMetrics()
repository = InMemoryStudyRepository(logger=logger)
ingestor: IngestorPort = PMCAdapter(logger=logger) | MockIngestorAdapter()
evaluator: EvaluatorPort = GemmaOllamaAdapter(logger=logger, cache=InMemoryCache(), metrics=metrics) | MockEvaluatorAdapter()
use_case = EvaluateStudyUseCase(ingestor, evaluator, repository, logger, clock, ScoringService, metrics)
```

* All wiring happens here.
* Use case is constructed via keyword arguments — easy to extend with new ports.
* The `--mock` branch goes through the use case (no domain bypass). R-03 verified.

**Verdict: ✅ Clean composition root.** Phase 2's FastAPI `main.py` should reuse this pattern via `Depends()` factories.

---

## 9. Layering / folder drift vs `FitSci - Directory Structure.md`

| Documented path | Actual path | Status |
|---|---|---|
| `adapters/logging/stdlib_logger.py` | `adapters/system/logger.py` | ⚠️ Drift |
| `adapters/clock/system_clock.py` | `adapters/system/clock.py` | ⚠️ Drift |
| `adapters/cache/in_memory_cache.py` | `adapters/cache/in_memory_cache.py` | ✅ |
| `adapters/metrics/jsonl_metrics.py` | *(not in the doc tree)* | ⚠️ Missing from doc |
| `adapters/ai/gemma_replay.py` | `adapters/ai/gemma_replay.py` | ✅ — but **hosts an `IngestorPort`** (see below) |

**Layering concern (R-14, doc + structure):**

* `adapters/ai/gemma_replay.py` defines both `GemmaReplayAdapter` (`EvaluatorPort`) and `ReplayIngestorAdapter` (`IngestorPort`). An `IngestorPort` implementation under `ai/` is mis-shelved.
* `adapters/ai/mock.py` defines `MockEvaluatorAdapter` and `MockIngestorAdapter`. Same issue.

The directory taxonomy promises *one folder per port family*. Recommended:

```
adapters/scrapers/
  mock.py            → MockIngestorAdapter
  replay.py          → ReplayIngestorAdapter
adapters/ai/
  mock.py            → MockEvaluatorAdapter (kept)
  gemma_replay.py    → GemmaReplayAdapter (kept)
```

And update `FitSci - Directory Structure.md` to reflect the real `adapters/system/` and `adapters/metrics/` folders.

---

## 10. New findings (post-remediation)

| ID | Finding | Severity | Phase-2 blocker? |
|---|---|---|---|
| **R-12** | `EvaluatorPort.evaluate_text -> Study` is over-broad; introduce `ExtractionResult` | Medium | No (but unlocks stricter type-level Judge invariant) |
| **R-13** | Cache / metrics are baked into `GemmaOllamaAdapter`; future adapters re-implement plumbing. Refactor to `CachedEvaluator` / `MeteredEvaluator` decorators | Medium | No (Phase 2 hardening) |
| **R-14** | `IngestorPort` adapters live under `adapters/ai/`; folder taxonomy drift | Small | No |
| **R-15** | `NullLogger` is in `adapters/system/`; consider moving it to `domain/ports/logger.py` so adapters don't import each other | Small | No |
| **R-16** | `FitSci - Directory Structure.md` shows `adapters/logging/` and `adapters/clock/` paths that no longer match reality | Small (doc) | No |
| **R-17** | Optional: add `backend/tests/unit/test_imports.py` AST guard so the domain-dependency rule is CI-enforced, not reviewer-enforced | Small | No |

None of these block Phase 2 scaffolding. R-12 and R-13 are the highest-leverage refactors because they harden the LLM-swap story *before* a second evaluator adapter exists.

---

## 11. Recommended next steps (in priority order)

1. **R-13 — Decorator-style cross-cutting evaluators** (~2 h). Pre-condition for adding `GemmaVertexAIAdapter` cleanly.
2. **R-12 — `ExtractionResult` model + port signature change** (~3 h, includes test updates). Makes the deterministic-Judge invariant type-level.
3. **R-14 + R-16 — Fold replay/mock ingestors into `adapters/scrapers/` and refresh the directory doc** (~1 h).
4. **R-17 — AST import guard for `domain/`** (~1 h). Cheap and durable.
5. **R-15 — Move `NullLogger` next to `LoggerPort`** (~30 min).

After (1)–(5), the architectural score moves from **8.0 → 9+**, and the "5-line LLM swap" promise becomes literally true rather than "true if you remember to re-wire the decorators."

---

## 12. Verification commands re-run

```bash
cd backend
python -m pytest --cov --cov-report=term-missing   # 42 passed, 1 skipped, 83% total
python -m pytest tests/test_scoring.py --cov=src.domain.services.scoring --cov-fail-under=90  # 99%
ruff check .                                       # clean
mypy --strict src                                  # clean
rg "from src.adapters" backend/src/domain          # 0 hits  ← domain rule
rg "from src.adapters" backend/src/application     # 0 hits  ← application rule
```

All checks green. Hexagonal contract holds; the remaining findings are refinements, not violations.
