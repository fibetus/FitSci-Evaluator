# 01 — Phase 0 DoD Verification

The Development Plan (`docs/FitSci - Development Plan.md` lines 107–114) marks all eight Phase 0 DoD items as `[x]`. Each is verified below against the actual source tree.

---

## 0.1 — All four ADRs committed at `docs/adr/`

**Verdict:** `✅ Confirmed`

**Evidence**

| ADR | File | Status field | Length |
|---|---|---|---|
| 0001 — Hexagonal architecture | `docs/adr/0001-architecture-hexagonal.md:1` | `Accepted` (line 3) | 65 lines, all sections present |
| 0002 — Scoring canonical spec | `docs/adr/0002-scoring-canonical-spec.md:1` | `Accepted` (line 3) | 68 lines, all sections present |
| 0003 — PostgreSQL JSONB | `docs/adr/0003-database-postgres-jsonb.md:1` | `Accepted` (line 3) | 90 lines, all sections present |
| 0004 — Gemma 4 12B Q4_K_M | `docs/adr/0004-gemma4-12b-q4km.md:1` | `Accepted` (line 3) | 83 lines, all sections present |

A fifth ADR, `0005-extraction-accuracy-f1-metric.md`, was added on 2026-05-10 and post-dates Phase 0. Its presence does not invalidate this DoD item but is flagged separately in [`04-documentation-integrity.md §5.1`](./04-documentation-integrity.md) for non-conformance to the README template.

---

## 0.2 — `Research Evaluation Model.md` and `scoring_basis.md` reconcile

**Verdict:** `✅ Confirmed`

**Evidence**
* `docs/FitSci - Research Evaluation Model.md` lines 3–12 explicitly carry a status header that designates the 0–14 spec as "v1 — implemented" and the 0–20 spec as "v2 — conceptual / not yet implemented". Lines 22, 47 reinforce the v1/v2 distinction inside the body.
* `docs/scoring_basis.md` lines 1–4 declare itself the source of truth compiled from `backend/src/domain/services/scoring.py` and `backend/tests/test_scoring.py`.
* No section of `Research Evaluation Model.md` claims the 0–20 criteria are active.

The seven-component matrix in `scoring_basis.md` lines 12–47 is in 1:1 correspondence with `scoring.py` lines 32–91; see [`04-documentation-integrity.md §5.2`](./04-documentation-integrity.md) for the per-row diff.

---

## 0.3 — `Study.flags` is `StudyFlags`, not `dict`

**Verdict:** `✅ Confirmed`

**Evidence**
* `backend/src/domain/models/study.py:51-55` declares `class StudyFlags(BaseModel)` with four typed fields.
* `backend/src/domain/models/study.py:106` declares `flags: StudyFlags = Field(default_factory=StudyFlags)` on the `Study` aggregate.
* No `dict` or `Any` typing leaks anywhere on the field.
* `backend/tests/test_scoring.py:235` exercises `flags=StudyFlags(is_industry_funded=True, has_full_text=False)` to confirm the typed instance flows through scoring.

---

## 0.4 — `ScoringService` is pure (no mutation)

**Verdict:** `✅ Confirmed`

**Evidence**
* `backend/src/domain/services/scoring.py:8-15` declares `class ScoringResult(BaseModel)` with `model_config = ConfigDict(frozen=True)` — the result is structurally immutable.
* `backend/src/domain/services/scoring.py:19-148` — the function reads `study.*` attributes and never assigns to any of them. The function returns a freshly constructed `ScoringResult` (lines 143–148).
* `backend/tests/test_scoring.py:222-244` (`test_calculate_rigor_index_does_not_mutate_study`) explicitly asserts `study.model_dump() == before` after a call.

⚠️ Adjacent finding (not a Phase 0 DoD violation, but relevant to §0.4's *spirit*): `backend/src/application/use_cases/evaluate_study.py:40,49-53` mutates the input `Study` returned by the evaluator. This is a *use-case-layer* mutation, not a domain-service mutation, so DoD 0.4 is honored. See [`03-architectural-integrity.md §4.4`](./03-architectural-integrity.md) for the architectural implication.

---

## 0.5 — `domain/ports/logger.py` and `domain/ports/clock.py` exist with `Protocol` definitions

**Verdict:** `✅ Confirmed`

**Evidence**
* `backend/src/domain/ports/logger.py:4` — `class LoggerPort(Protocol)`. Methods `info`, `warning`, `error`, `with_context` all use `...` body (Protocol idiom).
* `backend/src/domain/ports/clock.py:5` — `class ClockPort(Protocol):` with `now() -> datetime`.
* Both files import only `typing.Protocol` and stdlib `datetime`.

---

## 0.6 — `domain/errors.py` exists with the full error taxonomy

**Verdict:** `✅ Confirmed`

**Evidence** (`backend/src/domain/errors.py`)

| Class | Line |
|---|---|
| `FitSciError` (base) | 1 |
| `IngestionError` | 5 |
| `ExtractionError` | 9 |
| `ValidationError` | 13 |
| `RepositoryError` | 17 |
| `ConfigurationError` | 21 |

All five classes prescribed by `docs/FitSci - Cross-Cutting Concerns.md` lines 96–112 are present.

⚠️ Adjacent finding: `backend/src/application/use_cases/evaluate_study.py` does **not** import any class from `domain.errors`; it catches bare `Exception` (lines 33, 42, 55, 63). See `R-02` in [`07-remediation-plan.md`](./07-remediation-plan.md).

---

## 0.7 — CI workflow exists; local checks pass

**Verdict:** `⚠️ Partial`

**Evidence — what is correct**
* `.github/workflows/ci.yml:28` runs `python -m pytest`.
* `.github/workflows/ci.yml:31` runs `ruff check .`.
* `.github/workflows/ci.yml:34` runs `mypy --strict src` (with `working-directory: backend` set at line 14, this is equivalent to the documented `mypy --strict backend/src/`).

**Evidence — what is missing**

The CI baseline specified in `docs/FitSci - Cross-Cutting Concerns.md §11` lines 280–284 lists four required steps. The repo implements three:

| Required by §11 | Implemented in `ci.yml`? |
|---|---|
| `pytest backend/ --cov --cov-fail-under=80` | ⛔ No `--cov` flag; no `--cov-fail-under`. |
| `ruff check backend/` | ✅ |
| `mypy --strict backend/src/` | ✅ |
| `git diff --exit-code docs/scoring_basis.md` if `scoring.py` changed | ⛔ Not present in `ci.yml`. The `.githooks/pre-commit:12-18` enforces this *locally* if `core.hooksPath` is configured; CI does not. |

The DoD says "CI workflow exists" — strictly true. But the project's own Cross-Cutting Concerns doc and Plan §7 ("CI enforces consistency: any diff in `scoring.py` requires a touched `scoring_basis.md`") both demand more than the present YAML provides. Marking this `⚠️ Partial` rather than `✅ Confirmed` because the DoD's referenced source-of-truth (`§11`) is not satisfied.

---

## 0.8 — `.env.example` committed; `.env` is `.gitignore`d

**Verdict:** `✅ Confirmed`

**Evidence**
* `.env.example` — present at repository root, 24 lines, lists every variable required by adapters (`OLLAMA_BASE_URL`, `GEMMA_MODEL_TAG`, `NCBI_API_KEY`, `RATE_LIMIT_PER_MINUTE`, etc.).
* `.gitignore:151` — `.env` is in the `# Environments` block, alongside `.envrc`, `.venv`, `env/`, `venv/`.
* `.githooks/pre-commit:20-26` adds an extra defense: rejects commits whose staged diff matches `AKIA*`, `gho_*`, `sk-*`, or JWT patterns.

---

## Additional Phase 0 checks (not in the DoD checklist)

### Are `domain/ports/` exclusively Protocol-based?

**Verdict:** `✅ Confirmed`. Every file in `backend/src/domain/ports/` declares `class XxxPort(Protocol)` (`clock.py:5`, `evaluator.py:6`, `ingestor.py:4`, `logger.py:4`, `repository.py:6`). No `abc.ABC`, no `dataclass`, no concrete classes.

### Is the application-layer skeleton appropriately empty for Phase 0?

**Verdict:** `⚠️ Partial — note for the historical record`. The Phase 0 task description says: *"Create `backend/src/application/use_cases/` with an empty `EvaluateStudyUseCase`"* (Plan line 97). The current `backend/src/application/use_cases/evaluate_study.py` is 69 lines of fully-wired Phase-1 code. Because Phase 1 is also being verified in this audit, and the file is appropriate to *Phase 1*, this is not a DoD violation in the traditional sense — but it does mean the audit cannot distinguish between "Phase 0 left a real skeleton" and "Phase 0 was actually completed with Phase 1 work mixed in." If timeline integrity matters, the git history should be inspected to confirm Phase 0 left a skeleton that Phase 1 then expanded.

### Does `scoring.py` import from `adapters/` or `infrastructure/`?

**Verdict:** `✅ Confirmed clean`. `backend/src/domain/services/scoring.py:1-3` imports only `pydantic` and `..models.study`. No `httpx`, no `ollama`, no `adapters.*`, no `random`, no `datetime`. The deterministic-Judge invariant holds.

---

## Phase 0 summary

| Item | Verdict |
|---|---|
| 0.1 Four ADRs | ✅ Confirmed |
| 0.2 Doc reconciliation | ✅ Confirmed |
| 0.3 `StudyFlags` | ✅ Confirmed |
| 0.4 Pure scoring | ✅ Confirmed |
| 0.5 `LoggerPort` + `ClockPort` | ✅ Confirmed |
| 0.6 `domain/errors.py` | ✅ Confirmed |
| 0.7 CI workflow | ⚠️ Partial |
| 0.8 `.env.example` / gitignore | ✅ Confirmed |

**Phase 0 honest count:** 7 ✅ + 1 ⚠️ = **7.5 / 8 = 93.75%**.

This is the strongest part of the audit. The single partial is the missing scoring-spec consistency check in CI, which is an explicit, named requirement in `docs/FitSci - Cross-Cutting Concerns.md §11` and is also a checked-but-not-quite-done item in `docs/adr/0002-scoring-canonical-spec.md:62-63`.
