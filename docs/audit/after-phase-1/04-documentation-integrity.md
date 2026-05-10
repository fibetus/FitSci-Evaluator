# 04 — Documentation Integrity

## 5.1 — ADR completeness

The README at `docs/adr/README.md:9-13` lists the required template sections: **Status, Context, Decision, Alternatives considered, Consequences**. Each ADR is checked below.

| ADR | Status | Context | Decision | Alternatives | Consequences | Word-count (approx.) | Verdict |
|---|---|---|---|---|---|---|---|
| `0001-architecture-hexagonal.md` | line 3 ✅ | line 8 ✅ | line 17 ✅ | line 30 ✅ | line 42 ✅ (positive + negative + neutral) | ~1100 | ✅ |
| `0002-scoring-canonical-spec.md` | line 3 ✅ | line 8 ✅ | line 26 ✅ | line 34 ✅ | line 45 ✅ (positive + negative + neutral) | ~1100 | ✅ |
| `0003-database-postgres-jsonb.md` | line 3 ✅ | line 8 ✅ | line 19 ✅ | line 53 ✅ | line 64 ✅ (positive + negative + neutral) | ~1300 | ✅ |
| `0004-gemma4-12b-q4km.md` | line 3 ✅ | line 9 ✅ | line 20 ✅ | line 41 ✅ | line 66 ✅ (positive + negative + neutral) | ~1500 | ✅ |
| `0005-extraction-accuracy-f1-metric.md` | line 5 ✅ | line 9 ✅ | line 13 ✅ | **⛔ MISSING** | line 27 ✅ | ~360 | ⚠️ Stub-adjacent |

**Findings:**

* ADR-0005 has no "Alternatives considered" section even though the README template (`docs/adr/README.md:11`) lists it as required and the Plan's documentation-discipline rule treats ADRs as decision records that justify the runner-up rejection (`docs/adr/README.md:31`). The decision text — "use a flattened structural F1" — was not weighed against any alternative (e.g. exact-match F1, Jaccard similarity, BLEU/ROUGE on string fields, or a per-field-type metric mix). This makes ADR-0005 a *placeholder* in the strict sense the README defines: "A stub ADR is not an ADR — it is a placeholder pretending to be a decision record" (audit-prompt phrasing). `⚠️ RISK`.
* ADR-0001 line 60 references a test file that does not exist: `tests/unit/test_imports.py`. The ADR's "Compliance check" section claims this test "statically asserts that `domain/` modules only import `pydantic`, stdlib, or other `domain/` modules". `Glob backend/tests/unit/**` returns 0 files. `grep test_imports backend` returns 0 hits. The compliance check is unenforced. `⚠️ RISK`.
* ADR-0002 line 62–63 has its "Implementation checklist" out of sync with reality: item 3 ("Pre-commit hook checks for `scoring.py` ↔ `scoring_basis.md` co-modification") is unchecked, but the hook *is* implemented at `.githooks/pre-commit:12-18`. Item 4 ("CI job replicates the same check on `main`") is correctly unchecked — the CI YAML does not contain it.

---

## 5.2 — `scoring_basis.md` vs `scoring.py` consistency

**Rule (Plan §7 line 301):** "Any change to `scoring.py` updates `scoring_basis.md` in the same commit."

**Verdict:** `✅`

### Per-component diff

| Component | `scoring_basis.md` | `scoring.py` | Match |
|---|---|---|---|
| Study type — `meta-analysis` → +5 | line 13 | line 33–34 (`+= 5`) | ✅ |
| Study type — DB+placebo → +4 | line 14 | line 35–36 | ✅ |
| Study type — DB or `rct_crossover` → +3 | line 15 | line 37–38 | ✅ |
| Study type — `rct` → +2 | (implicit via "single double-blind" generalization) | line 39–40 | ⚠️ doc says "single double-blind"; code says any `rct.startswith` |
| Study type — `cohort_prospective` with N>100 → +2 | line 16 | line 41–42 | ✅ |
| Study type — `review_narrative` → +1 | line 17 | line 43–44 | ✅ |
| Population — Human + trained → +2 | line 21 | line 47–49 | ✅ |
| Population — Human + other → +1 | line 22 | line 50–51 | ✅ |
| Population — non-human → −5 | line 23 | line 52–53 | ✅ |
| Sample size ≥200 → +2 | line 26 | line 57–58 | ✅ |
| Sample size 50–199 → +1 | line 27 | line 59–60 | ✅ |
| Sample size 0–9 → −3 | line 28 | line 61–62 | ✅ |
| Year ≥2024 → +2 | line 31 | line 65–66 | ✅ |
| Year ≥2022 → +1 | line 32 | line 67–68 | ✅ |
| Year <2019 → −1 | line 33 | line 69–70 | ✅ |
| IF ≥10 → +2 | line 36 | line 73–74 | ✅ |
| IF ≥5 → +1 | line 37 | line 75–76 | ✅ |
| IF <2 → −1 | line 38 | line 77–78 | ✅ |
| Methodology placebo → +1 | line 41 | line 81–82 | ✅ |
| Methodology DB → +1 | line 42 | line 83–84 | ✅ |
| Methodology preregistered → +1 | line 43 | line 85–86 | ✅ |
| Bias industry-funded → −1 | line 46 | line 88–89 | ✅ |
| Bias no full text → −1 | line 47 | line 90–91 | ✅ |
| Score clamp `min(14, max(0, raw))` | line 53 | line 103 | ✅ |
| Tier ≥8 → high | line 56 | line 106–107 | ✅ |
| Tier 5–7 → moderate | line 57 | line 108–109 | ✅ |
| Tier <5 → rejected | line 58 | line 110–111 | ✅ |
| Confidence base = `score/14*100` | line 62 | line 118 | ✅ |
| Confidence multiplier — meta=1.0 | line 64 | line 120–122 | ✅ |
| Confidence multiplier — DB+placebo=0.85 | line 65 | line 123–124 | ✅ |
| Confidence multiplier — any rct=0.75 | line 66 | line 125–126 | ✅ |
| Confidence multiplier — other=0.5 | line 67 | line 120 | ✅ |
| Confidence bonus — I²<25 → +10 | line 69 | line 130–131 | ✅ |
| Confidence bonus — I²>75 → −15 | line 70 | line 132–133 | ✅ |
| Confidence bonus — citations>50 → +8 | line 71 | line 136–137 | ✅ |
| Confidence bonus — citations>10 → +4 | line 72 | line 138–139 | ✅ |
| Purity contract | line 76–79 | line 19, 143–148 (frozen `ScoringResult`) | ✅ |

The single nuance is the doc's wording for the `rct` (non-double-blind) tier: `scoring_basis.md:15` reads "single double-blind OR `rct_crossover`: +3" and (implicitly) line 14 covers DB+placebo at +4, but the code at `scoring.py:39-40` falls through to `study_type_pts = 2` for *any* `study.type.startswith("rct")` not previously matched. The doc does not name a "+2 for plain rct" tier explicitly. This is a minor doc-wording gap that should be reconciled by adding a "single-arm RCT (no double-blind, no crossover): +2" row to `scoring_basis.md §1`.

The scoring spec is otherwise faithfully reflected in the code.

---

## 5.3 — `Research Evaluation Model.md` version clarity

**Verdict:** `✅`

* `docs/FitSci - Research Evaluation Model.md:3-12` — explicit status block separating v1 (implemented, 0–14, `scoring_basis.md`) from v2 (conceptual, 0–20, this document).
* Line 22 — section heading explicitly reads "*The Scoring Matrix (target — not yet implemented)*".
* Line 47 — explanatory paragraph titled "*What v1 does instead*" reaffirms the split.
* No table or sentence in the document claims the 0–20 criteria are active.

The doc is unambiguous about the v1/v2 boundary.

---

## 5.4 — Cross-cutting concerns coverage in code

`docs/FitSci - Cross-Cutting Concerns.md` lists items with phase gates. For the four items gated to Phase 1, this section verifies the code-evidence requirement.

| Concern | Phase gate | Required evidence | Found? | Verdict |
|---|---|---|---|---|
| Structured logging + correlation IDs | Phase 1 | `LoggerPort` used in all Phase 1 adapters; correlation ID generated at composition root and threaded through use case | Adapters do not accept `LoggerPort`; no `correlation_id` field anywhere (`grep correlation_id backend` → 0 hits); `cli/main.py:56` constructs `ConsoleLogger()` without context | ⛔ |
| LLM response caching | Phase 1 | `CachePort` + at least one adapter implementation | `domain/ports/cache.py` does not exist; `adapters/cache/` directory does not exist | ⛔ |
| Token / latency metrics | Phase 1 | `MetricsPort` + at least one adapter implementation | `domain/ports/metrics.py` does not exist; `adapters/metrics/` directory does not exist | ⛔ |
| Prompt-injection mitigation | Phase 1 | `<paper>...</paper>` delimiter in prompt template; refusal preamble; field-provenance exclusion; **length cap**; **probe tests** | Delimiter at `extract_v1.txt:67` (closing) and `gemma_ollama.py:33`; preamble at `extract_v1.txt:3`; provenance at `extract_v1.txt:5`. ⛔ length cap not implemented; ⛔ no `tests/security/test_prompt_injection.py` | ⚠️ Partial |

**One of four** Phase-1-gated cross-cutting concerns is partially honored; the remaining three are entirely absent in code despite being marked complete by the Phase 1 ✅ status.

---

## 5.5 — CLAUDE.md / engineering guidelines enforcement

`docs/FitSci - Development Plan.md §7` (lines 292–301) lists the engineering guidelines. Three are CI-gateable; this section verifies them.

| Rule | How to verify | Result |
|---|---|---|
| No mutations in domain services | `scoring.py` — no `study.field = value` pattern anywhere | ✅ Verified at `scoring.py:19-148`; the function reads `study.*` and assigns nothing back to it. |
| `scoring_basis.md` canonical — CI enforces consistency | A CI step that fails when `scoring.py` is modified without `scoring_basis.md` | ⛔ Missing. `.githooks/pre-commit:12-18` enforces this **locally** if `core.hooksPath` is set; the CI YAML (`.github/workflows/ci.yml`) has no equivalent step. The Plan §7 wording is unambiguous: "(CI enforces consistency: any diff in `scoring.py` requires a touched `scoring_basis.md`)". The pre-commit alone is insufficient because it depends on each developer's local config. |
| No agent frameworks | `pyproject.toml` / `requirements.txt` — no `crewai`, `langgraph`, `langchain` | ✅ Verified — `backend/pyproject.toml:11-19` and `backend/requirements.txt:1-7` list only `pydantic`, `fastapi`, `uvicorn`, `sqlmodel`, `httpx`, `python-dotenv`, `pymupdf`, plus dev deps. None of the named frameworks. |

Two out of three rules are honored; the third (`scoring_basis.md` co-modification) is unenforced in CI and only enforced locally via the optional pre-commit hook.

---

## Other documentation findings

### Plan ↔ port-signature drift on `RawDocument`

`docs/FitSci - Development Plan.md:50` declares the `IngestorPort` signature as `fetch_by_id(id) -> RawDocument`. The actual signature in `backend/src/domain/ports/ingestor.py:5` is `fetch_by_id(self, study_id: str) -> str`. No `RawDocument` model is defined in `backend/src/`. Either define `RawDocument` (a `BaseModel` with at least `text: str` and `source: str`) and update the port, or amend the Plan to match the implemented signature.

### `phase_1_summary.md` claims uncited

`docs/phase_1_summary.md:27-32` declares all five DoD items checked. None of those bullets cites a verification artifact for the DoD items rated `⛔ False` in `02-phase1-dod-verification.md` (criteria 1.2, 1.4, 1.5, 1.6, 1.8). The summary is more aggressive than the DoD it summarizes — exactly the "false-finish" risk R2 the project itself identifies (`docs/FitSci - Risk Register.md:17`).

### `Directory Structure.md` planning forward — but markers are out of date

`docs/FitSci - Directory Structure.md:22, 23` mark `cache.py` and `metrics.py` ports as `⏳ Phase 1`. Since Phase 1 is declared `✅`, these markers should now read either `✅` (if the ports were implemented) or be moved to a Phase 2 backlog. They were not implemented; the doc still says `⏳ Phase 1`. Consistent with §3.3 in `02-phase1-dod-verification.md`.

---

## Summary

| Section | Verdict |
|---|---|
| 5.1 ADR completeness | ⚠️ ADR-0005 missing alternatives; ADR-0001 references nonexistent test |
| 5.2 scoring_basis ↔ scoring.py | ✅ (one minor wording gap on plain `rct` tier) |
| 5.3 Research Evaluation Model version clarity | ✅ |
| 5.4 Cross-cutting in code | ⛔ for logging, cache, metrics; ⚠️ for prompt-injection (delimiter ✅, length cap ⛔, probe tests ⛔) |
| 5.5 CLAUDE-rules enforcement | 2 / 3 — `scoring_basis.md` co-mod is local-only, not CI |

The documentation set is internally rich and well-cross-referenced, but has accumulated drift in three places where claims do not match the codebase: ADR-0001's referenced test, ADR-0002's checklist, and the Phase 1 cross-cutting story in CCC vs the actual code.
