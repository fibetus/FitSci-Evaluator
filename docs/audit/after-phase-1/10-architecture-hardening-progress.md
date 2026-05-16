# 10 — Architecture Hardening Progress (R-12 … R-17)

> Implements findings from [`09-architectural-integrity-recheck.md`](./09-architectural-integrity-recheck.md). Last updated: 2026-05-16.

## Target score

| Metric | Before | After |
|---|---|---|
| Architectural integrity (§09) | 8.0 / 10 | **9.2 / 10** |

---

## Checklist

| ID | Item | Status | Evidence |
|---|---|---|---|
| R-15 | `NullLogger` colocated with `LoggerPort` | ✅ | `domain/ports/logger.py`; removed `adapters/system/null_logger.py` |
| R-14 | Ingestor adapters under `adapters/scrapers/` | ✅ | `scrapers/replay.py`, `scrapers/mock_ingestor.py` |
| R-12 | `ExtractionResult` + `EvaluatorPort → ExtractionResult` | ✅ | `domain/models/extraction.py`; use case `into_study()` |
| R-13 | `CachedEvaluator` / `MeteredEvaluator` decorators | ✅ | `adapters/ai/cached_evaluator.py`, `metered_evaluator.py`; CLI `_build_evaluator()` |
| R-16 | Directory structure doc matches code | ✅ | `docs/FitSci - Directory Structure.md` |
| R-17 | AST domain import guard in CI | ✅ | `tests/unit/test_imports.py` |

---

## LLM swap (verified)

Composition root (`cli/main.py`):

```python
base = GemmaOllamaAdapter(logger=logger)
cached = CachedEvaluator(base, InMemoryCache(), model_tag=base.model_tag)
evaluator = MeteredEvaluator(cached, metrics=metrics, model=base.model_tag)
```

To add Vertex AI: replace `GemmaOllamaAdapter` with `GemmaVertexAIAdapter` only — cache and metrics decorators stay.

---

## Re-verification commands

```bash
cd backend
python -m pytest --cov --cov-report=term-missing
python -m pytest tests/unit/test_imports.py -v
rg "from src.adapters" src/domain src/application
ruff check .
mypy --strict src
```

Expected: 44+ tests pass, 83% coverage, zero adapter imports in domain/application.
