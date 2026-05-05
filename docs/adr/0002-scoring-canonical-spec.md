# ADR-0002 — `scoring_basis.md` is the canonical spec for the implemented Judge

* **Status:** Accepted
* **Date:** 2026-05-06
* **Decision drivers:** spec/code drift surfaced in [`audit-architecture.md §3`](../internal/audit/audit-architecture.md); contributor confusion risk from two coexisting Rigor Index definitions.
* **Related:** [`scoring_basis.md`](../scoring_basis.md), [`FitSci - Research Evaluation Model.md`](../FitSci%20-%20Research%20Evaluation%20Model.md).

## Context

Two scoring specifications exist in the repo:

1. **v1 — implemented in code** (`backend/src/domain/services/scoring.py`):
   - 0–14 scale.
   - Built on study type tier, population (human / trained), sample size, recency, impact factor, methodology bonuses, bias flags.
   - Documented in `docs/scoring_basis.md`.

2. **v2 — conceptual / scientific target** (`docs/FitSci - Research Evaluation Model.md`):
   - 0–20 scale.
   - Anchored on MRI vs DEXA, trained vs untrained, Cohen's d, 95% CI width — derived from *"Badania naukowe w treningu siłowym: interpretacja"*.
   - **Not yet implemented.** Requires schema fields the current `Study` model does not have (e.g. `measurement_tool`).

The audit ([`audit-architecture.md §3`](../internal/audit/audit-architecture.md)) flagged this as the project's most dangerous drift: anyone reading the product narrative would expect a different Judge than the one that ships.

A previous code reference to a missing `GEMINI.md` file made this worse. That reference has been replaced with a citation of `scoring_basis.md`, but the doc-side reconciliation still needs to be made formal so it cannot regress.

## Decision

1. **`docs/scoring_basis.md` is the authoritative description of the Judge as implemented (v1).**
2. **`docs/FitSci - Research Evaluation Model.md` is the authoritative description of the long-term science target (v2).** It is explicitly labeled as "not yet implemented" in its header.
3. **Code citations.** Any docstring in `backend/src/domain/services/scoring.py` that references a scoring spec **must** cite `scoring_basis.md`. No reference to `GEMINI.md`, `Research Evaluation Model.md`, or any other location.
4. **Consistency rule (CI-enforced).** A PR that modifies `backend/src/domain/services/scoring.py` **must** also modify `docs/scoring_basis.md` in the same commit, or be explicitly labeled `[no-scoring-change]` in the commit body. Pre-commit hook + CI job enforce this.
5. **Migration v1 → v2** is described in [`FitSci - Research Evaluation Model.md §1`](../FitSci%20-%20Research%20Evaluation%20Model.md): five-step plan ending in an `/api/v2/` cutover. v2 cannot ship until Phase 1 DoD 1.3 (≥80% field-level F1) is met for the new fields.

## Alternatives considered

* **Keep both specs equally authoritative.**
  Rejected: this is the status quo that produced the drift. Two equal sources of truth = silent contradiction.

* **Delete `Research Evaluation Model.md` and standardize on v1.**
  Rejected: it would discard the scientific narrative that motivates the project (MRI-vs-DEXA, trained-vs-untrained — the source PDF's core insights). The narrative is part of why FitSci exists.

* **Reverse course: implement v2 immediately, delete v1.**
  Rejected for now. The v2 schema requires fields Gemma cannot reliably extract until benchmark accuracy is proven (Phase 1 DoD 1.3). Implementing v2 prematurely would push the false-finish risk (R2) into the scoring layer, not just the data layer.

## Consequences

### Positive
* **Single source of truth for code.** New contributors cannot accidentally implement the wrong scoring rules — they read `scoring_basis.md` and the test suite, both of which reflect what runs.
* **Scientific roadmap stays explicit.** v2 is not abandoned; it is the documented target with a measurable entry condition.
* **CI enforcement prevents regression.** The "any change to `scoring.py` requires touching `scoring_basis.md`" rule kills the drift class entirely.

### Negative
* **Two specs to keep in sync conceptually.** Mitigated by clear "implemented vs target" labeling in the headers and by routine review at the end of each phase.

### Neutral
* The README and Development Plan now reference both: v1 for what runs, v2 for where we're going. This is verbose but unambiguous.

## Implementation checklist

* [x] `Research Evaluation Model.md` carries a v1/v2 status header.
* [x] `scoring_basis.md` is referenced in `scoring.py` docstring.
* [ ] Pre-commit hook checks for `scoring.py` ↔ `scoring_basis.md` co-modification (Phase 0).
* [ ] CI job replicates the same check on `main` (Phase 0).
* [ ] Once v2 ships, this ADR is superseded by `ADR-NNNN-scoring-v2-cutover.md`.

---

*Superseded by:* (none yet)
