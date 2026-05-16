# 00 — Audit Index (Post-Phase-1)

> ⛔ **PROJECT HEALTH WARNING:** The Development Plan's claimed completion status is materially misleading. Phase 1 is marked `✅` (`docs/FitSci - Development Plan.md` line 122) but five of eight Phase 1 acceptance criteria (1.2, 1.4, 1.5, 1.6, 1.8) and three of three Phase 1 cross-cutting requirements (logger correlation IDs, `CachePort`, `MetricsPort`) are unmet by `⛔ False` rather than `⚠️ Partial`.

| Field | Value |
|---|---|
| Date | 2026-05-10 |
| Audited by | Claude Opus (automated adversarial audit) |
| Audit type | post-Phase-1 |
| Repository commit context | working tree at the time of read |
| Honest completion rate | **~91%** after remediation — see [`08-remediation-progress.md`](./08-remediation-progress.md) |
| Overall project health score | **8.5 / 10** (post architecture hardening) |

---

## Project health score (5.5 / 10) — justification

The project's *foundation* is largely solid: the hexagonal layering is clean (`backend/src/domain/` imports nothing outside stdlib + Pydantic — confirmed in `03-architectural-integrity.md §4.1`), the deterministic Judge is genuinely pure (`scoring.py` lines 1–3), the `Study` aggregate is properly typed including `StudyFlags`, and Phase 0 DoD items 0.1, 0.3, 0.4, 0.5, 0.6, 0.8 are all honestly complete.

The score is dragged down because the Phase 1 verification surface — the surface that *proves* the system works — is largely absent:

* `tests/integration/test_pipeline.py` referenced in DoD 1.2 does not exist.
* `tests/test_scoring.py::test_determinism` referenced in DoD 1.5 does not exist.
* `tests/security/test_prompt_injection.py` referenced in DoD 1.8 does not exist.
* The 90% coverage gate on `scoring.py` (DoD 1.4) is configured nowhere.
* The 80% F1 benchmark (DoD 1.3) is real code in `backend/tests/benchmark/test_extraction_accuracy.py` line 96–101 but is `pytest.skip`-gated by `RUN_BENCHMARK=1` (line 97–100), runs nowhere in CI, and has therefore never been demonstrated.
* Three Phase-1 cross-cutting ports (logging in adapters, `CachePort`, `MetricsPort`) are missing entirely.

This is not "Phase 1 is 90% done with a small T6 gap"; it is "Phase 1 has built the load-bearing components but skipped the contracts that prove they bear load."

---

## Top 3 blockers

| ID | Finding | File:line |
|---|---|---|
| **B-01** | Three Phase-1 verification tests promised by DoD 1.2 / 1.5 / 1.8 do not exist. The Development Plan claims Phase 1 is `✅` (line 122) and the README claims so too (line 63). | DoD source: `docs/FitSci - Development Plan.md` lines 152, 155, 158 |
| **B-02** | DoD 1.4 (`≥90% line coverage on scoring.py`) is enforced nowhere. `.github/workflows/ci.yml` line 28 runs `pytest` with no `--cov` flag; `backend/pyproject.toml` declares `pytest-cov` (line 23) but configures no threshold. The DoD's own self-verification command (`pytest --cov=src.domain.services.scoring --cov-fail-under=90`) is in no script. | `backend/pyproject.toml:23`, `.github/workflows/ci.yml:28` |
| **B-03** | Three cross-cutting Phase-1 ports listed as **hard requirements** in `docs/FitSci - Development Plan.md` lines 142–144 are missing: (i) `LoggerPort` is not threaded through `PMCAdapter` or `GemmaOllamaAdapter`; no correlation ID is generated anywhere (`grep correlation_id` → 0 hits). (ii) `domain/ports/cache.py` does not exist. (iii) `domain/ports/metrics.py` does not exist. | `backend/src/adapters/scrapers/pmc.py:20–30`, `backend/src/adapters/ai/gemma_ollama.py:14–25`, missing files |

---

## Top 3 risks (independent of blockers)

| ID | Finding | File:line |
|---|---|---|
| **R-01** | `EvaluateStudyUseCase` mutates the `Study` returned by the evaluator (lines 40, 49–53) instead of returning a new aggregate. Combined with the application-layer location of these mutations, the deterministic-Judge story has a small leak: if the evaluator already populated a field (`score`, `confidence`, `quality_tier`), it is overwritten, but the mutation pattern means use-case retries are not idempotent on the same input. | `backend/src/application/use_cases/evaluate_study.py:40,49-53` |
| **R-02** | `EvaluateStudyUseCase` does not enforce the `domain/errors.py` taxonomy — every `try` block catches bare `Exception` (lines 33, 42, 55, 63) and re-raises. Adapters do wrap exceptions correctly, but the use case's contract permits any third-party exception to escape. The promise in `docs/FitSci - Cross-Cutting Concerns.md` line 116 ("Adapters must not leak third-party exception types upward") becomes contingent on adapter discipline alone, with no use-case-level enforcement. | `backend/src/application/use_cases/evaluate_study.py:33,42,55,63` |
| **R-03** | The `--mock` branch in `backend/src/cli/main.py` (lines 23–50) calls `ScoringService.calculate_rigor_index` directly, bypassing `EvaluateStudyUseCase`. This is the canonical "CLI calls the domain directly" anti-pattern called out in `docs/FitSci - Development Plan.md` line 80, gated only by a CLI flag rather than removed. | `backend/src/cli/main.py:45` |

---

## Honest assessment of Phase 1 completion

Phase 1 is **not complete by its own DoD**. The CLI runs against real adapters (DoD 1.1 ✅), the linter / type-checker / unit-test pipeline runs in CI (DoD 1.7 ✅), and the structural code (`PMCAdapter`, `GemmaOllamaAdapter`, `EvaluateStudyUseCase`, fixtures) is in place. But of the eight acceptance criteria that gate the phase, three are partial-or-better and five are `⛔ False` — meaning the corresponding test, coverage gate, latency benchmark, or security probe simply does not exist in the codebase.

The phase summary in `docs/phase_1_summary.md` lines 27–32 declares all DoD items met. None of those bullets cites a verification artifact for criteria 1.2, 1.4, 1.5, 1.6, or 1.8. The Development Plan in line 140 claims `Task 6 complete` with an F1 ≥ 80% threshold; the test exists but is unconditionally skipped in CI by an environment-variable guard (`backend/tests/benchmark/test_extraction_accuracy.py:97`), so the threshold has never been demonstrated against live Gemma output. Closing this honestly requires either (a) running the harness with a recorded `GemmaReplayAdapter` so it executes in CI, or (b) explicitly downgrading T6 in the plan to "harness scaffolded; awaiting first measurement."

The recommended remediation order is in [`07-remediation-plan.md`](./07-remediation-plan.md). Three of those items (`B-01`, `B-02`, `B-03`) block the integrity of the Phase 1 ✅ claim itself; everything else is incremental hardening for Phase 2 entry.

---

## Report files

| File | Contents |
|---|---|
| [`01-phase0-dod-verification.md`](./01-phase0-dod-verification.md) | Item-by-item verdict on Phase 0 DoD 0.1–0.8 plus additional checks |
| [`02-phase1-dod-verification.md`](./02-phase1-dod-verification.md) | Item-by-item verdict on Phase 1 tasks T1–T6, criteria 1.1–1.8, and cross-cutting requirements |
| [`03-architectural-integrity.md`](./03-architectural-integrity.md) | Hexagonal dependency rule, port completeness, application-layer rule, determinism, Extract & Discard, port scope, DI |
| [`04-documentation-integrity.md`](./04-documentation-integrity.md) | ADR audit, scoring spec ↔ scoring.py diff, version-clarity check, cross-cutting coverage, CLAUDE-rules enforcement |
| [`05-test-quality.md`](./05-test-quality.md) | Test inventory, integration-test honesty, security-test depth, coverage configuration, missing coverage list |
| [`06-dod-honesty-table.md`](./06-dod-honesty-table.md) | The full DoD honesty table with a per-row verdict and the 65.9% honest completion rate |
| [`07-remediation-plan.md`](./07-remediation-plan.md) | Per-finding fix specification with effort estimate and Phase-2-blocking flag |
| [`08-remediation-progress.md`](./08-remediation-progress.md) | Remediation checklist with verification commands (2026-05-16) |
| [`09-architectural-integrity-recheck.md`](./09-architectural-integrity-recheck.md) | Post-remediation hexagonal contract re-check; LLM-swap verification; R-12 … R-17 |
| [`10-architecture-hardening-progress.md`](./10-architecture-hardening-progress.md) | R-12 … R-17 implementation checklist (2026-05-16) |

*All findings cite a file path and line number. Confidence levels are stated in-line whenever a finding could not be verified due to a missing file.*
