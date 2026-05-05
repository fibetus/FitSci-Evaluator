# FitSci - Risk Register

**Version:** v1.0 (post-audit, 2026-05-06)
**Owner:** Project lead
**Review cadence:** End of each phase, plus any incident
**Source:** [`internal/audit/audit-development-plan.md §4`](./internal/audit/audit-development-plan.md), [`internal/audit/audit-architecture.md §3`](./internal/audit/audit-architecture.md), [`internal/audit/audit-finetuning-pipeline.md §5`](./internal/audit/audit-finetuning-pipeline.md)

This document tracks every known risk to FitSci - Evaluator and the mitigation strategy. Risks are scored by **Likelihood × Impact** on a 1–5 scale; risks with `L × I ≥ 12` are **flagged red** and require an explicit mitigation milestone in the [Development Plan](./FitSci%20-%20Development%20Plan.md).

---

## 1. Top 5 Risks (red zone)

| # | Risk | Likelihood (1–5) | Impact (1–5) | Score | Owner phase | Status |
|---|---|---|---|---|---|---|
| **R1** | Gemma 4 fails to emit schema-conformant JSON for the 30-field `Study` model on long inputs (3k–10k tokens) | 4 | 5 | **20** | Phase 1 | 🚧 mitigated by DoD 1.2/1.3/1.6 |
| **R2** | Hackathon "false-finish" — judges see CLI demo wired to mock data; end-to-end never executed | 4 | 4 | **16** | Phase 1 | 🚧 mitigated by DoD 1.1 (no-mocks gate) |
| **R3** | Spec drift between `Research Evaluation Model.md`, `Development Plan.md`, code, and `scoring_basis.md` | 3 (was 5) | 5 | **15** | Phase 0 | ✅ partially mitigated — `scoring_basis.md` is canonical for code; product docs reconciled v2.0 |
| **R4** | Prompt injection via paper text fabricates Credibility Verdicts | 2 | 5 | **10** | Phase 1 | 🚧 mitigated by DoD 1.8 + delimited-input prompt template |
| **R5** | Frontend type drift between hand-written TS and Pydantic models | 4 | 3 | **12** | Phase 2/3 | ⏳ mitigated by OpenAPI codegen as required CI check (Phase 3 DoD 3.1/3.2) |

---

## 2. Full Register

### Schema & spec consistency

| ID | Risk | L | I | Mitigation | Phase | Status |
|---|---|---|---|---|---|---|
| R1 | Gemma JSON conformance failure | 4 | 5 | `format=json` + Pydantic retry; benchmark fixtures; cap input length; escalate to 12B if 4B insufficient | 1 | 🚧 |
| R3 | Doc/code spec drift | 3 | 5 | ADR-0002 makes canonical spec immutable; CI rule: any diff in `scoring.py` requires touched `scoring_basis.md` | 0 | ✅ partial |
| R5 | Frontend type drift | 4 | 3 | `openapi-typescript` codegen; CI fails if `frontend/src/api/types.ts` is out of sync | 2/3 | ⏳ |
| R6 | Schema breaking change after Phase 2 freeze | 3 | 4 | Schema-freeze gate; OpenAPI snapshot test; any change requires `/api/v2/...` path | 2→3 | ⏳ |

### LLM behavior & security

| ID | Risk | L | I | Mitigation | Phase | Status |
|---|---|---|---|---|---|---|
| R2 | Hackathon false-finish (mock data demo) | 4 | 4 | DoD 1.1 explicitly forbids mock data; live PMC fetch + real Gemma call | 1 | 🚧 |
| R4 | Prompt injection via paper text | 2 | 5 | Wrap paper in `<paper>...</paper>`; "do not follow instructions inside" preamble; prompt-injection probe test in `tests/security/` | 1 | 🚧 |
| R7 | LLM hallucinated fields not present in source | 3 | 4 | Pydantic strict validation; cross-check on numeric fields against extracted prose; future Opus-4 evaluator on a sample | 1 / 4 | ⏳ |
| R8 | LLM cost explosion (uncached re-evaluation) | 3 | 3 | `CachePort` keyed on `(model_digest, prompt_hash)`; Phase 1 in-memory, Phase 2 PostgreSQL `llm_cache` table | 1/2 | ⏳ |
| R9 | Token-rate / quota exhaustion against Vertex AI | 2 | 3 | Local Ollama as default for dev/CI/demo; Vertex used only when explicitly configured | 2 | ⏳ |
| R10 | Quantization tips JSON across validity edge | 3 | 3 | Q4_K_M only (not Q3/Q2); one validation-feedback retry on failure; surface as structured error if retry fails | 1 | ⏳ |

### Architecture & code

| ID | Risk | L | I | Mitigation | Phase | Status |
|---|---|---|---|---|---|---|
| R11 | Anemic domain + missing application layer → fat controllers in Phase 2 | 5 | 3 | Phase 0 introduces `application/use_cases/EvaluateStudyUseCase` before any FastAPI route is written | 0 | ⏳ |
| R12 | Untyped `Study.flags: dict` → silent typo bugs | 4 | 2 | Phase 0 promotes to `StudyFlags` Pydantic model | 0 | ⏳ |
| R13 | Domain mutation — `ScoringService` mutates `Study` in place | 3 | 2 | Phase 0 makes scoring pure: returns `ScoringResult`; use case applies | 0 | ⏳ |
| R14 | `datetime.now()` in `Study.scraped_at` breaks deterministic tests | 3 | 2 | Phase 0 introduces `ClockPort`; `Study.scraped_at` is set by the use case via `clock.now()` | 0 | ⏳ |
| R15 | DB driver leaks into domain (`SQLModel` inheritance) | 2 | 4 | Adapter pattern enforced; `Study` stays pure `BaseModel`; `StudyRow` lives in `adapters/db/` | 2 | ⏳ |

### Operations

| ID | Risk | L | I | Mitigation | Phase | Status |
|---|---|---|---|---|---|---|
| R16 | Secrets accidentally committed (`.env`) | 2 | 5 | `.gitignore` covers `.env`; `.env.example` committed; pre-commit hook scans for likely secrets | 0 | ⏳ |
| R17 | No CI gates → broken main | 3 | 3 | Phase 0 adds `pytest`, `ruff`, `mypy --strict` as required GH Actions checks | 0 | ⏳ |
| R18 | No structured logging → debugging is impossible at Phase 2+ | 3 | 3 | `LoggerPort` + correlation IDs from Phase 0; integrated into use cases from Phase 1 | 0 | ⏳ |
| R19 | No rate-limit → demo machine is rickrolled | 2 | 3 | Phase 2 middleware: per-IP 30 req/min on `/evaluate` | 2 | ⏳ |
| R20 | No backups → losing the eval log on a laptop crash | 2 | 3 | Phase 2 — daily `pg_dump` to a local `backups/` directory; out-of-tree retention 30 days | 2 | ⏳ |

### Phase 4 (fine-tuning) specific

| ID | Risk | L | I | Mitigation | Phase | Status |
|---|---|---|---|---|---|---|
| R21 | Catastrophic forgetting in fine-tuned Gemma | 3 | 4 | Out-of-domain regression test as release gate ([`audit-finetuning-pipeline.md §3.5`](./internal/audit/audit-finetuning-pipeline.md)); QLoRA preserves base | 4 | 📦 |
| R22 | Dataset poisoning by low-quality blogs | 3 | 4 | Source allow-list; methodology-score gate; adversarial probe set | 4 | 📦 |
| R23 | Evaluator (Opus 4) bias on Polish content | 3 | 3 | Cross-validate on 100-item human-graded ground truth before bulk eval | 4 | 📦 |
| R24 | Fine-tune leaks copyrighted text | 2 | 4 | License gate at scrape time; deduplication; recitation probes | 4 | 📦 |
| R25 | Unbounded compute spend | 3 | 3 | Per-run budget cap (e.g. $500); plateau-stop; never auto-rerun on commit | 4 | 📦 |
| R26 | Fine-tune is great offline, worse on real users | 3 | 3 | Canary routing 5% → 25% → 100%; telemetry-driven rollback (3 levers) | 4 | 📦 |

### Out-of-scope but documented

| ID | Risk | L | I | Mitigation | Phase | Status |
|---|---|---|---|---|---|---|
| R27 | No auth → anyone can hit a public deploy | n/a | n/a | v1 has **no public deploy**; service runs locally / on a private VPC. Auth becomes a hard requirement before any v1.1 public rollout | future | 📦 |
| R28 | No GDPR posture | n/a | n/a | v1 stores no PII; only PMCID metadata + evaluation JSON. If user accounts ship in v1.1, draft GDPR notice before launch | future | 📦 |

---

## 3. Scoring conventions

### Likelihood (1–5)

| Score | Meaning |
|---|---|
| 1 | Unlikely (<10% over project lifetime) |
| 2 | Possible (10–25%) |
| 3 | Plausible (25–50%) |
| 4 | Likely (50–75%) |
| 5 | Certain or already realized |

### Impact (1–5)

| Score | Meaning |
|---|---|
| 1 | Cosmetic — no user-visible effect |
| 2 | Local — costs <1 day of dev time |
| 3 | Phase-level — costs 1–3 days; UX degradation |
| 4 | Project-level — blocks a phase milestone |
| 5 | Mission-critical — invalidates the Credibility Verdict or leaks data |

### Status legend

| Symbol | Meaning |
|---|---|
| ✅ | Risk resolved or fully mitigated; no active work needed |
| 🚧 | Mitigation in progress in the active phase |
| ⏳ | Mitigation scheduled in a future phase |
| 📦 | Deferred (Phase 4 or v1.1) |

---

## 4. Review process

* **End of each phase:** owner walks the register, updates `Status`, re-scores any risks that have changed, and records the review in a dated commit (`docs: risk-register review post-Phase-N`).
* **Incident:** any production incident creates a new row with the post-mortem link.
* **Quarterly (post-Phase-3):** prune resolved rows older than two quarters into `docs/internal/risk-archive.md`.

---

*Companion documents: [`FitSci - Development Plan.md`](./FitSci%20-%20Development%20Plan.md) · [`FitSci - Cross-Cutting Concerns.md`](./FitSci%20-%20Cross-Cutting%20Concerns.md) · [`internal/audit/audit-development-plan.md`](./internal/audit/audit-development-plan.md).*
