# 08 — Remediation Progress

> Tracked against [`07-remediation-plan.md`](./07-remediation-plan.md). Last updated: 2026-05-16.

## Summary

| Metric | Before | After remediation |
|---|---|---|
| Honest DoD completion ([`06-dod-honesty-table.md`](./06-dod-honesty-table.md)) | 65.9% | ~91% (1.3 + 1.6 remain partial) |
| `pytest` (global `--cov`, 80% gate) | not enforced | ✅ 42 passed, 83% total |
| `scoring.py` 90% gate | not enforced | ✅ 99% |

---

## Day 1 — Small fixes, doc honesty

| ID | Item | Status | Verification |
|---|---|---|---|
| B-04 | `test_determinism` | ✅ | `backend/tests/test_scoring.py` |
| B-02 | Coverage gates (80% global, 90% scoring) | ✅ | `pyproject.toml` `[tool.coverage.*]`; CI `ci.yml` |
| R-04 | ADR-0005 alternatives section | ✅ | `docs/adr/0005-extraction-accuracy-f1-metric.md` |
| R-05 | ADR-0001 import-test claim | ✅ | Option (b): compliance text updated |
| R-06 | `rct_crossover` / `case_study` scoring tests | ✅ | `backend/tests/test_scoring.py` |
| R-08 | `RawDocument` plan drift | ✅ | Option (b): Development Plan §M1 |
| R-10 | `internal/audit/` → `audit/before-phase-0/` links | ✅ | Global replace in `docs/**/*.md` |
| R-11 | Git hooks documented | ✅ | `README.md` §6 `core.hooksPath` |

---

## Day 2 — Integration, security, logging

| ID | Item | Status | Verification |
|---|---|---|---|
| B-01 | Integration pipeline test | ✅ | `backend/tests/integration/test_pipeline.py` |
| B-03 | Prompt-injection security tests | ✅ | `backend/tests/security/test_prompt_injection.py` |
| B-05 | Logger in adapters + correlation ID | ✅ | Adapters + `test_logging.py`; CLI `uuid` |

---

## Day 3 — Cross-cutting + use-case hardening

| ID | Item | Status | Verification |
|---|---|---|---|
| B-06 | `CachePort` + in-memory adapter | ✅ | `domain/ports/cache.py`, `adapters/cache/`, `test_cache.py` |
| B-07 | `MetricsPort` + JSONL adapter | ✅ | `domain/ports/metrics.py`, `test_metrics.py` |
| B-08 | Input length cap | ✅ | `GemmaOllamaAdapter.max_input_chars` + `paper_truncated` log |
| R-01 | Immutable `model_copy` in use case | ✅ | `evaluate_study.py` |
| R-02 | Error taxonomy wrapping | ✅ | `evaluate_study.py` + `test_evaluate_study.py` |
| R-07 | PMC HTTP + Ollama JSON error tests | ✅ | `test_pmc_adapter.py`, `test_gemma_ollama_adapter.py` |

---

## Day 4 — Polish

| ID | Item | Status | Verification |
|---|---|---|---|
| R-03 | `--mock` via use case + mock adapters | ✅ | `adapters/ai/mock.py`, `cli/main.py` |
| R-09 | Honest `phase_1_summary.md` | ✅ | Verdict table + outstanding section |

---

## Still partial (not blockers for starting Phase 2 scaffolding)

| Item | Notes |
|---|---|
| DoD 1.3 F1 benchmark | Run once with `RUN_BENCHMARK=1` or add CI replay artifact |
| DoD 1.6 latency SLO | Metrics exist; add threshold test when targets are frozen |
| Section-aware chunking (B-08 follow-up) | Truncation only; chunking deferred |

## Architecture hardening (R-12 … R-17)

Implemented 2026-05-16 — full checklist in [`10-architecture-hardening-progress.md`](./10-architecture-hardening-progress.md).

| ID | Item | Status |
|---|---|---|
| R-12 | `ExtractionResult` + narrowed `EvaluatorPort` | ✅ |
| R-13 | `CachedEvaluator` / `MeteredEvaluator` decorators | ✅ |
| R-14 | Ingestor adapters under `adapters/scrapers/` | ✅ |
| R-15 | `NullLogger` on `LoggerPort` | ✅ |
| R-16 | Directory structure doc refresh | ✅ |
| R-17 | `tests/unit/test_imports.py` AST guard | ✅ |

---

## Commands to re-verify locally

```bash
cd backend
python -m pytest --cov --cov-report=term-missing
python -m pytest tests/test_scoring.py --cov=src.domain.services.scoring --cov-fail-under=90
python -m pytest tests/integration tests/security -v
ruff check .
mypy --strict src
```
