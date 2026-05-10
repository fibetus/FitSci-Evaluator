# Audit — Hexagonal Architecture

**Date:** 2026-05-02
**Last reviewed by:** Claude Opus (automated audit)
**TL;DR:** The hexagonal blueprint is sound on paper. The **implemented** Rigor Index is now fully auditable: `docs/scoring_basis.md` matches `backend/src/domain/services/scoring.py`, and `calculate_rigor_index` points to that file. What remains is **cross-document drift**: `FitSci - Research Evaluation Model.md` and `FitSci - Development Plan.md` still describe a 0–20 / MRI-vs-DEXA model that is *not* what the code runs—readers must treat `scoring_basis.md` as the source of truth for the Judge (M3) until product docs are reconciled.

---

## 1. Summary

The project explicitly chose **Option A: Hexagonal (Ports & Adapters)** in `FitSci - Technical Architecture.md` and codified the layout in `FitSci - Directory Structure.md`. The directory plan is textbook hexagonal: `domain/{models,services,ports}` isolated from `adapters/{ai,scrapers,db,api}`, with two entrypoints (`cli/main.py`, `main.py`).

Current implementation status (verified against `backend/src/`):
- ✅ `domain/models/study.py`, `domain/services/scoring.py`, `domain/ports/{ingestor,evaluator,repository}.py` exist.
- ❌ `adapters/` directory does not exist yet — no `GemmaAdapter`, no `PMCAdapter`, no `SQLModelAdapter`, no FastAPI controllers.
- ⚠️ `cli/main.py` instantiates a hardcoded mock `Study` and bypasses the Ingestor/Evaluator ports entirely. This is acceptable for a Phase 1 milestone but means the port contract has never been exercised end-to-end.

The architecture is therefore **planned correctly but only ~30% implemented**. For the Judge (M3), **implementation ↔ documentation is now aligned** via `docs/scoring_basis.md` (see §3 for the remaining mismatch with older narrative docs).

---

## 2. Criterion-by-Criterion Ratings

| # | Criterion | Rating | Evidence |
|---|---|---|---|
| 1 | Clear domain boundaries, no infra leakage | ⚠️ Risk | `domain/models/study.py` imports `pydantic.BaseModel`. Pydantic is a third-party library, technically a violation of the "pure Python, no external deps" rule stated in `FitSci - Directory Structure.md` line 9. Pragmatic but undocumented as a deliberate exception. |
| 2 | Ports separated from adapters | ✅ Good | All three ports use `typing.Protocol` (structural typing), which is the lightest possible interface contract. `EvaluatorPort.evaluate_text`, `RepositoryPort.{save,get_by_id,list_all}`, and `IngestorPort.{fetch_by_id,search}` are correctly minimal. |
| 3 | Dependency rule (domain → zero outer deps) | ⚠️ Risk | `scoring.py` and `study.py` import only from within `domain/`, which is correct. However, the design relies on Pydantic for validation — fine, but the rule should be amended in docs to "domain depends only on Pydantic and stdlib." |
| 4 | Phase ordering — domain first, then app, then infra | ✅ Good | `FitSci - Development Plan.md` Phase 1 explicitly sequences: Domain Models → The Judge (M3, pure logic) → The Sifter (M2, adapter) → CLI. This is correct inside-out hexagonal sequencing. |
| 5 | Frontend integration via UI adapter | ⚠️ Risk | `FitSci - Directory Structure.md` shows `frontend/` as a sibling of `backend/`, communicating via JSON HTTP. This is correct headless decoupling. **However**, no API contract document, no OpenAPI version pinning, and no Pydantic-to-TypeScript codegen plan exist. The "Data Alignment" step in Phase 3 (`Plan §4.3.1`) is one line and undefined. |
| 6 | Anti-pattern check (anemic domain, fat controllers, ORM in domain) | ⚠️ Risk | The `Study` domain model is **anemic**: it is purely a data container with no behavior. All logic lives in `ScoringService` as static methods on the model. This is acceptable in Python/Pydantic projects but is the canonical "anemic domain model" anti-pattern (Fowler). For a hackathon it is fine; for the production roadmap it should be flagged. |
| 7 | Application/Use-Case layer | ❌ Problem | There is **no application layer**. `cli/main.py` directly orchestrates domain services and constructs domain objects, mixing the role of a use-case orchestrator with that of a CLI adapter. In strict hexagonal you want `application/use_cases/evaluate_study.py` between the CLI and the domain. |
| 8 | Spec ↔ implementation consistency | ⚠️ Risk | **Code path is clear:** `docs/scoring_basis.md` documents the same rules as `scoring.py`, and the docstring references that file. **Product docs still diverge:** `FitSci - Research Evaluation Model.md` / `FitSci - Development Plan.md` describe a different 0–20 / methodology-heavy Rigor Index — see §3. |

---

## 3. Critical Issues

### ✅ Resolved (for code) — Implemented Rigor Index is documented
- **`docs/scoring_basis.md`** records the full point matrix, quality tiers, and confidence formula used by `ScoringService.calculate_rigor_index` in `backend/src/domain/services/scoring.py`. The method docstring now cites `docs/scoring_basis.md` instead of the former `GEMINI.md` reference.
- **`tests/test_scoring.py`** exercises the same rules (e.g. meta-analysis + trained + large-N expectations).
- The earlier **opaque `GEMINI.md` gap** is closed for practical purposes: auditors and contributors no longer need a missing file to understand what the Judge does in code.

### ⚠️ Remaining — Cross-document drift (product narrative vs running code)
- `FitSci - Research Evaluation Model.md` still defines a **0–20** Rigor Index grounded in *MRI vs DEXA*, *Trained vs Untrained*, *Cohen's d*, *95% CI width* (methodology from the source PDF).
- `FitSci - Development Plan.md` still states a **0–20** score with MRI/DEXA framing.
- The **running implementation** is the matrix in `scoring_basis.md` (raw points summed into `study.score`, normalized in confidence with a `/14` divisor, study-type / IF / recency / flags—not the PDF’s full methodological checklist).

**Impact:** Anyone who reads only the narrative research/plan docs will expect a different Judge than the one shipped. **`scoring_basis.md` is the authoritative description of M3 as implemented** until `Research Evaluation Model.md` and the Development Plan are updated, superseded, or explicitly split into “conceptual model (v2)” vs “implemented matrix (v1).”

### ⛔ BLOCKER 2 — README contradicts current stack
`README.md` (lines 52–57) lists the technology stack as "LangChain / LlamaIndex" and "Streamlit / Gradio". But:
- `FitSci - Stack Analysis.md` *explicitly rejects* Streamlit ("Do not use Streamlit. It will kill the unique visual identity") and prescribes FastAPI + React.
- `FitSci - Development Plan.md` `§5` says "Avoid complex AI agent frameworks (like CrewAI/LangGraph) if simple prompt-chaining in M2 suffices."

The README is the entry point for any new contributor or judge. It is now lying about the architecture.

### ⚠️ Risk 3 — Anemic domain + missing application layer
`ScoringService.calculate_rigor_index` mutates the passed `Study` in place and returns it. This is a static method that:
1. Knows the structure of `ScoreBreakdown`,
2. Mutates `study.score`, `study.score_breakdown`, `study.quality_tier`, `study.confidence`,
3. Bypasses any use-case-level transaction or audit logging.

For an evaluator system whose entire selling point is *traceable methodology*, the absence of an `EvaluateStudyUseCase` (which would compose Ingestor → Evaluator → Scorer → Repository, log inputs/outputs, and emit a domain event) is a structural gap that will become painful in Phase 2.

### ⚠️ Risk 4 — `scoring.py` accesses `study.flags["is_industry_funded"]` via dict key
`Study.flags: dict` (line 98 of `study.py`) is an untyped `dict[str, Any]`. The scoring engine does `study.flags.get("is_industry_funded")` — silent typo risk, no IDE assistance, no validation. This belongs in a Pydantic sub-model (`StudyFlags`).

### ⚠️ Risk 5 — Frontend↔Backend type drift is unguarded
Phase 3 step 1 is "Update the existing React `Study` type to match the Python Pydantic models" — described in one bullet point. There is no plan for:
- Schema versioning (`/v1/studies`)
- Codegen (Pydantic → OpenAPI → TypeScript via e.g. `openapi-typescript`)
- Contract tests

Given the `Study` model has 30+ fields with nested `Population`, `Delta`, `Dosage`, `ScoreBreakdown` objects, manual hand-syncing is guaranteed to drift.

---

## 4. Recommendations

### 4.1 Immediate (before any more code is written)
1. **Reconcile product docs with `scoring_basis.md`.** The code side is no longer ambiguous. Choose one of:
   - (a) **Doc alignment:** Edit `FitSci - Research Evaluation Model.md` and `FitSci - Development Plan.md` to state that the **implemented** Rigor Index is defined in `docs/scoring_basis.md`, and move the 0–20 / MRI–DEXA material to a clearly labeled section (e.g. “Target model — not yet implemented” or “v2 roadmap”).
   - (b) **Code alignment:** Replace `scoring.py` (and tests) with the 0–20 methodology from `Research Evaluation Model.md`, then rewrite `scoring_basis.md` to match—only if that model is explicitly chosen as the new canonical behavior.
   - In both cases, record the decision in `/docs/adr/0001-scoring-canonical-spec.md` so the split between “narrative science doc” and “executable Judge” cannot regress silently.
2. **Rewrite `README.md`** to match `FitSci - Stack Analysis.md`: FastAPI + React + Gemma + PostgreSQL. Remove Streamlit/Gradio/LangChain mentions.
3. **Add a one-paragraph "Pydantic exception"** clause to `FitSci - Directory Structure.md` documenting that the domain depends on Pydantic by deliberate choice (it's behaving as a domain-validation library, not as infra).

### 4.2 Architectural fixes (Phase 1 → Phase 2 boundary)
4. **Introduce an application layer.** Create `backend/src/application/use_cases/evaluate_study.py` with a single `EvaluateStudyUseCase` class that takes the three ports as constructor args and exposes one `execute(study_id: str) -> Study` method. CLI and FastAPI controllers should call *this*, not the domain directly.
5. **Promote `Study.flags` to a typed `StudyFlags` Pydantic model.** Eliminate the `dict[str, Any]`.
6. **Make scoring pure**, not mutating. `calculate_rigor_index(study) -> ScoringResult` returning a frozen result object the use case applies. Easier to test, easier to audit, no hidden mutation.

### 4.3 Frontend integration safeguards
7. **Auto-generate the OpenAPI schema** from FastAPI (`/openapi.json`) and run `openapi-typescript` in the frontend build. Commit the generated `api.ts`. Type drift becomes a compile error, not a runtime bug.
8. **Version the API path** from day one (`/api/v1/studies`). The Bio-Signal frontend is being migrated from a separate project — when its data model is fixed against `v1`, future schema evolution doesn't break it.

### 4.4 Cross-cutting
9. **Add an ADR folder.** `/docs/adr/` is referenced nowhere yet. Critical decisions already made (hexagonal over layered, FastAPI over Streamlit, PostgreSQL over SQLite, Pydantic in domain) should each become an ADR. Without them, every future contributor will re-litigate these choices.
10. **Define a logging port** (`LoggerPort`) and a **clock port** (`ClockPort`) in `domain/ports/`. `Study.scraped_at = datetime.now()` (line 105 of `study.py`) couples the domain to wall-clock time, breaking deterministic tests.

---

*End of architecture audit.*
