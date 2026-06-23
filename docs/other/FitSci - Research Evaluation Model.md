# FitSci - Research Evaluation Models: Proposals & Justifications

> **Status note (2026-05-06).** This document captures the **scientific target** for the Judge — the long-term vision derived from *"Badania naukowe w treningu siłowym: interpretacja"*. It describes what we *want* the Judge to evaluate when the system is mature.
>
> **Two specs coexist by design:**
>
> | Layer | Source of truth | Scale | Status |
> |---|---|---|---|
> | **v1 — implemented Rigor Index** | [`docs/other/scoring_basis.md`](./scoring_basis.md) | **0–14** | What `backend/src/domain/services/scoring.py` runs *today*. Authoritative for any reader who wants to know what the code does. |
> | **v2 — conceptual Rigor Index** | this document, §1 | **0–20** | The PDF-grounded science target (MRI vs DEXA, Trained vs Untrained, Cohen's d, 95% CI). **Not yet implemented.** |
>
> **If `scoring_basis.md` and this document disagree, the implemented v1 spec wins for code; this document wins for the scientific roadmap.** The migration v1 → v2 is tracked in [`adr/0002-scoring-canonical-spec.md`](../adr/0002-scoring-canonical-spec.md).

This document presents three specialized models for evaluating scientific research within the FitSci ecosystem.

---

## 1. Proposal 1: The Rigor Index — v2 Conceptual (0–20 Points)

Focuses on the **methodological quality** and **statistical power** of the study.

### The Scoring Matrix (target — not yet implemented)

| Criterion | Metric | Points |
| :--- | :--- | :--- |
| **Evidence Level** | Meta-analysis / Position Stand | +6 |
| | RCT (Randomized Controlled Trial) | +4 |
| | Observational / Epidemiological | +1 |
| **Measurement Tool** | MRI (Gold Standard) | +4 |
| | Ultrasound (USG) | +2 |
| | DEXA (Lean Mass overestimation risk) | -1 |
| **Subject Status** | Resistance Trained (≥6 months) | +3 |
| | Untrained / Beginners | +1 |
| **Statistical Depth** | Cohen's d (Effect Size) reported | +3 |
| | Narrow Confidence Intervals (95% CI) | +2 |
| | Only p-value reported (p < 0.05) | +0 |
| | p-value > 0.05 | -5 |

### Why these choices?

* **MRI vs. DEXA:** the source PDF highlights that DEXA cannot distinguish actual muscle fibres from "cellular swelling" (water/glycogen) and overestimates results. MRI is the only tool for true cross-sectional area (CSA) measurement.
* **Trained vs. Untrained:** beginners respond to almost any stimulus (*Newbie Gains*), making it impossible to extrapolate to advanced lifters.
* **Cohen's d > p-value:** p-value tells you *if* a result is non-random; Cohen's d tells you *how strong* it is in the real world.

### What v1 does instead

The v1 implementation (`scoring_basis.md`) uses a **0–14 scale** anchored on different signals: study type tier, population (human/trained), sample size, recency, impact factor, methodology bonuses, and bias penalties. v1 is intentionally simpler because it was built before structured extraction of MRI-vs-DEXA / Cohen's d / 95% CI was reliable from Gemma. The v2 model requires those fields to be **reliably extracted** (Phase 1 DoD 1.3) before the matrix can be implemented faithfully.

### Migration plan v1 → v2

1. **Phase 1 must succeed first.** Field-level F1 ≥ 80% on `effect_size`, `effect_size_type`, `is_significant`, and the as-yet-unrepresented `measurement_tool` field.
2. **Schema evolution.** Add `measurement_tool: Literal["MRI","USG","DEXA","BIA","other"]` to `Study`. This is a breaking schema change → bump API to `/api/v2/`.
3. **Implementation swap.** Replace `ScoringService.calculate_rigor_index` with the v2 matrix; update `scoring_basis.md` to mirror it.
4. **Parallel-run window.** Run both v1 and v2 scorers in shadow for two weeks, compare verdict drift, document expected delta.
5. **Cutover.** Flip the production Judge to v2; keep v1 available behind a `?scorer=v1` query parameter for one minor version, then remove.

---

## 2. Proposal 2: The Integrity Filter (Flag-based)

Focuses on identifying **biases** and **statistical manipulation** (p-hacking).

### Logic flow

1.  **Funding source.** Industry-funded (e.g. supplement company) → ⚠️ **High Bias Alert**.
2.  **Conflict of interest.** Check for "Researcher Degrees of Freedom".
3.  **Heterogeneity (\(I^2\)).** Meta-analyses with \(I^2 > 50\%\) are "mixing apples with oranges" → flag as **Inconsistent Data**.
4.  **Surrogate outcomes.** Studies measuring acute spikes (e.g. MPS for 2h) rather than chronic adaptations (8-week hypertrophy) → flag as **Mechanistic Only**.

### Implementation status

- v1 already encodes a subset: `is_industry_funded` and `has_full_text` flags affect `bias_pts` (`scoring_basis.md §7`).
- The full Integrity Filter is the planned **P-Hacking Sniffer** feature (`audit-gemma4-features.md §4`) → a `Gemma 4B` adapter behind `IntegrityAuditorPort` produces an `IntegrityReport` that the deterministic Judge consumes. Score is *never* set by the LLM.

### Why these choices?

* **P-hacking awareness:** the source PDF warns researchers often "torture data until it confesses" p < 0.05. The filter looks for selective-reporting fingerprints.
* **MPS vs. growth:** acute Muscle Protein Synthesis does *not* always correlate with long-term hypertrophy.

---

## 3. Proposal 3: The APEASE Actionability Matrix

Translates scientific findings into **gym practice**.

### Evaluation categories

* **Practicality:** can this be done in a standard gym?
* **Effectiveness:** is the Effect Size (Cohen's d) at least "Medium" (>0.5)?
* **Acceptability:** would an athlete actually stick to this protocol?
* **Safety:** does the method increase injury risk?

### Implementation status

Currently surfaced through the `Study.practical_note` and `Study.caveats` free-text fields, which Gemma fills with prose. A structured APEASE matrix is part of the v2 roadmap — it requires the same upgrade path as v2 Rigor Index (more fields, breaking schema change, `/api/v2/`).

### Why these choices?

* **Goldman's Dilemma:** athletes will trade health for performance; this matrix prevents reckless implementation of experimental techniques.
* **Small effect sizes:** if a study shows a "statistically significant but practically tiny" result (d = 0.15), the system should advise: *"do not change your plan for this."*

---

## 4. Implementation in Gemma 4 (current pipeline)

The **FitSci Evaluator** uses these models to generate its "Credibility Verdict":

1. **Sifter (M2 / `EvaluatorPort`):** Gemma 4 extracts the structured `Study` (N, type, training status, effect size, p-value, IF, ...).
2. **Judge (M3 / `ScoringService`):** deterministic Python computes the Rigor Index. **v1 today, v2 when the migration plan in §1 is satisfied.**
3. **Interpretation (Phase 4 — `Lay Translator` and `Explainer`):** Gemma 4 4B renders a 3-sentence NTS-style summary in PL/EN; APEASE-style notes are populated.

The Judge is and remains deterministic. Gemma extracts and rephrases; the verdict belongs to math and humans, not to the LLM.

---

*Referenced document: Badania naukowe w treningu siłowym: interpretacja*

*Companion docs: [`scoring_basis.md`](./scoring_basis.md) (v1 implemented spec) · [`FitSci - Development Plan.md`](../architecture/FitSci%20-%20Development%20Plan.md) · [`adr/0002-scoring-canonical-spec.md`](../adr/0002-scoring-canonical-spec.md).*
