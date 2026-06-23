# Phase 1 Summary: The Core "Scientist" (CLI MVP)

## Overview

Phase 1 establishes the core pipeline of FitSci-Evaluator: fetching scientific papers, extracting structured data via a Large Language Model, and scoring them using a deterministic ruleset. The CLI is the composition root for the hexagonal pipeline.

## Completed work

1. **Ingestor (`PMCAdapter`)** — NCBI E-utilities with local XML cache under `~/.fitsci/cache/pmc/`.
2. **Evaluator (`GemmaOllamaAdapter`)** — Ollama JSON extraction with validation retry, prompt escaping, input truncation, `CachePort`, and `MetricsPort`.
3. **Replay / mock adapters** — `GemmaReplayAdapter` + `ReplayIngestorAdapter` for CI; `MockEvaluatorAdapter` + `MockIngestorAdapter` for offline CLI.
4. **Use case (`EvaluateStudyUseCase`)** — Ingest → evaluate → score → persist with immutable `model_copy` updates and domain error wrapping.
5. **Cross-cutting ports** — `LoggerPort` (correlation ID at CLI), `CachePort`, `MetricsPort` (JSONL).
6. **Verification** — Integration, security, determinism, and coverage gates in CI (see audit remediation progress).

## Definition of Done — honest status

| Criterion | Verdict | Evidence |
|---|---|---|
| 1.1 CLI real adapters | ✅ | `cli/main.py` wires `PMCAdapter` + `GemmaOllamaAdapter` |
| 1.2 Integration pipeline test | ✅ | `backend/tests/integration/test_pipeline.py` (5 fixtures) |
| 1.3 F1 ≥ 80% on benchmarks | ⚠️ Partial | Harness exists; requires `RUN_BENCHMARK=1` + live Ollama |
| 1.4 ≥ 90% coverage on `scoring.py` | ✅ | CI step `--cov-fail-under=90` on `tests/test_scoring.py` |
| 1.5 Determinism (100×) | ✅ | `tests/test_scoring.py::test_determinism` |
| 1.6 Latency targets | ⚠️ Partial | `MetricsPort` records latency; no enforced SLO test yet |
| 1.7 CI lint / typecheck / test | ✅ | `.github/workflows/ci.yml` |
| 1.8 Prompt-injection probes | ✅ | `backend/tests/security/test_prompt_injection.py` |
| CC: Logger + correlation ID | ✅ | `ConsoleLogger(correlation_id=…)` + adapter logs |
| CC: `CachePort` | ✅ | `InMemoryCache` + `tests/integration/test_cache.py` |
| CC: `MetricsPort` | ✅ | `JsonlMetrics` + evaluation metric tests |

**Outstanding before claiming full Phase 1 closure:** run the benchmark harness once with live Gemma (or commit a recorded replay) to demonstrate DoD 1.3; add latency SLO tests when DoD 1.6 thresholds are finalized.

## How to test offline

```bash
cd backend
python -m pytest --cov --cov-report=term-missing
python -m src.cli.main --mock PMC12345
```

Integration tests (no Ollama):

```bash
python -m pytest tests/integration tests/security -v
```

Benchmark (Ollama required):

```bash
# PowerShell
$env:RUN_BENCHMARK="1"; python -m pytest tests/benchmark/test_extraction_accuracy.py -v -s
```
