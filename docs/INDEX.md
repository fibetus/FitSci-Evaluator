# FitSci - Documentation Index

**Last updated:** 2026-05-06
**Purpose:** one-page navigation map. If you are reading this for the first time, follow the **Reading Order** in §1.

---

## 1. Reading Order (recommended onboarding path)

For a new contributor or judge to get from "what is this?" to "ready for Phase 1":

| # | Document | Reading time | Why now |
|---|---|---|---|
| 1 | [README.md](../README.md) | 5 min | Project pitch, quick links, local-run instructions |
| 2 | [FitSci - Evaluator context.md](./FitSci%20-%20Evaluator%20context.md) | 5 min | Product context — the problem, the solution, target audience |
| 3 | [FitSci - Stack Analysis.md](./FitSci%20-%20Stack%20Analysis.md) | 4 min | Why FastAPI + React + PostgreSQL (and why **not** Streamlit / LangChain / RAG) |
| 4 | [FitSci - Technical Architecture.md](./FitSci%20-%20Technical%20Architecture.md) | 4 min | Hexagonal vs Layered vs Modular Monolith — and why hexagonal won |
| 5 | [FitSci - Directory Structure.md](./FitSci%20-%20Directory%20Structure.md) | 6 min | Where each port and adapter lives (target structure with phase markers) |
| 6 | [FitSci - Development Plan.md](./FitSci%20-%20Development%20Plan.md) | 15 min | Master roadmap — Phase 0–4, measurable DoDs, time-boxes, risks |
| 7 | [FitSci - Cross-Cutting Concerns.md](./FitSci%20-%20Cross-Cutting%20Concerns.md) | 10 min | Logging, errors, caching, prompt-injection, secrets, CI — the unglamorous essentials |
| 8 | [FitSci - Risk Register.md](./FitSci%20-%20Risk%20Register.md) | 6 min | Top-5 risks with mitigations + the full register |
| 9 | [FitSci - Research Evaluation Model.md](./FitSci%20-%20Research%20Evaluation%20Model.md) | 6 min | Scoring science — v1 (what runs) vs v2 (target) |
| 10 | [scoring_basis.md](./scoring_basis.md) | 3 min | Canonical v1 scoring rules — the source of truth for what `scoring.py` does |
| 11 | [FitSci - Design.md](./FitSci%20-%20Design.md) | 4 min | Bio-Signal aesthetic, color tokens, component architecture |
| 12 | [adr/README.md](./adr/README.md) | 2 min | Index of architectural decisions |

If you are debugging or extending a specific area, jump straight to the matching folder in §2 / §3 / §4.

---

## 2. Documents in `docs/` (root)

> Top-level docs are the **operational truth** for product, architecture, and process.

| Document | What it answers | Status |
|---|---|---|
| [INDEX.md](./INDEX.md) (this file) | Where do I find anything? | Active |
| [FitSci - Evaluator context.md](./FitSci%20-%20Evaluator%20context.md) | What is this project, for whom, and why? | Active |
| [FitSci - Development Plan.md](./FitSci%20-%20Development%20Plan.md) | What ships in which phase, with what acceptance criteria? | Active — v2.0 (post-audit) |
| [FitSci - Technical Architecture.md](./FitSci%20-%20Technical%20Architecture.md) | What architectural pattern do we follow and why? | Active — Option A locked |
| [FitSci - Directory Structure.md](./FitSci%20-%20Directory%20Structure.md) | Where does each module live in the codebase? | Active — target structure with phase markers |
| [FitSci - Stack Analysis.md](./FitSci%20-%20Stack%20Analysis.md) | What stack did we pick, what did we reject, why? | Active — verdict locked |
| [FitSci - Research Evaluation Model.md](./FitSci%20-%20Research%20Evaluation%20Model.md) | What scientific scoring model do we aspire to (v2) and why? | Active — v2 conceptual target |
| [scoring_basis.md](./scoring_basis.md) | What scoring rules does the code actually run today (v1)? | **Canonical for code** |
| [FitSci - Design.md](./FitSci%20-%20Design.md) | Bio-Signal UI aesthetic, palette, components | Active |
| [FitSci - Cross-Cutting Concerns.md](./FitSci%20-%20Cross-Cutting%20Concerns.md) | Logging, errors, caching, prompt-injection, secrets, CI | Active — v1.0 |
| [FitSci - Risk Register.md](./FitSci%20-%20Risk%20Register.md) | What can go wrong, scored, with mitigations and owners | Active — v1.0 |

### Phase Summaries

| Document | Purpose | Status |
|---|---|---|
| [phase_1_summary.md](./phase_1_summary.md) | The Core "Scientist" MVP Phase 1 Summary & Walkthrough | ✅ Complete |

---

## 3. Architecture Decision Records (`docs/adr/`)

> ADRs are **append-only**. To revise a decision, write a new ADR that supersedes the old one.

| # | Title | Status | Date | Summary |
|---|---|---|---|---|
| [0001](./adr/0001-architecture-hexagonal.md) | Adopt Hexagonal (Ports & Adapters) | Accepted | 2026-05-06 | Pure domain + Protocol ports + adapters; Pydantic permitted in domain as a deliberate exception |
| [0002](./adr/0002-scoring-canonical-spec.md) | `scoring_basis.md` is the canonical Judge spec | Accepted | 2026-05-06 | v1 = `scoring_basis.md` (code); v2 = `Research Evaluation Model.md` (target). CI enforces co-modification |
| [0003](./adr/0003-database-postgres-jsonb.md) | PostgreSQL with JSONB-first schema | Accepted | 2026-05-06 | One row per `Study` aggregate; promoted columns for filtering; `pgvector` upgrade path |
| [0004](./adr/0004-gemma4-12b-q4km.md) | Gemma 4 12B Q4_K_M for production; 4B for CI/dev | Accepted | 2026-05-06 | Ollama (local/CI) ↔ Vertex AI (prod); 12B is the smallest variant reliably emitting nested 30-field JSON |
| [0005](./adr/0005-extraction-accuracy-f1-metric.md) | Extraction Accuracy F1 Metric | Accepted | 2026-05-10 | Flattened structural F1 metric computing partial matches for lists and strings |

ADR README and template guidance: [adr/README.md](./adr/README.md).

---

## 4. Internal Audit Reports (`docs/audit/before-phase-0/`)

> Independent reviews of the project's documentation and code. **Read these before changing anything architectural.** They are versioned at the date of audit and **not edited in place** afterwards.

| Document | Topic | Headline |
|---|---|---|
| [audit-index.md](./audit/before-phase-0/audit-index.md) | Executive summary | Project health 6.5/10; doc/code drift was the #1 risk (now mitigated by Phase 0) |
| [audit-architecture.md](./audit/before-phase-0/audit-architecture.md) | Hexagonal layering, ports, adapters, anti-patterns | Domain leaks, missing application layer, anemic `Study`, untyped `flags` |
| [audit-development-plan.md](./audit/before-phase-0/audit-development-plan.md) | Phase plan & cross-cutting gaps | Phases lacked DoD richness, time-boxes, cross-cutting concerns — addressed in v2.0 of the plan |
| [audit-database.md](./audit/before-phase-0/audit-database.md) | Database choice & repository port design | PostgreSQL JSONB-first; anti-patterns to avoid (SQLModel inheritance, raw text storage, integer IDs) |
| [audit-gemma4-selection.md](./audit/before-phase-0/audit-gemma4-selection.md) | Variant + quantization + deployment + upgrade thresholds | 12B Q4_K_M production; 4B Q4_K_M dev/CI; quantitative 27B-upgrade triggers |
| [audit-gemma4-features.md](./audit/before-phase-0/audit-gemma4-features.md) | Six concrete Phase-4 features | Per-feature variant sizing; one feature → one port; deterministic-Judge invariant preserved |
| [audit-finetuning-pipeline.md](./audit/before-phase-0/audit-finetuning-pipeline.md) | Hermes scrape → Opus 4 evaluation → QLoRA → A/B-tested deploy | QLoRA on 12B; routing adapter behind one port; rollback levers and budget caps |

---

## 5. Private / non-public materials (`docs/internal/private/`)

> Not committed publicly (gitignored content): the source PDF and an internal `CLAUDE.md` brief.

| File | Purpose |
|---|---|
| `Badania naukowe w treningu siłowym_ interpretacja.pdf` | Source methodology document grounding the Rigor Index v2 conceptual model |
| `CLAUDE.md` | Internal AI-assistant brief — engineering style, do/don't list |

---

## 6. Cross-references — "Where do I learn about X?"

| Topic | Primary doc | Supporting docs |
|---|---|---|
| **Project pitch** | [README.md](../README.md) | [Evaluator context.md](./FitSci%20-%20Evaluator%20context.md) |
| **Why hexagonal?** | [ADR-0001](./adr/0001-architecture-hexagonal.md) | [Technical Architecture.md](./FitSci%20-%20Technical%20Architecture.md), [audit-architecture.md](./audit/before-phase-0/audit-architecture.md) |
| **Where does file X live?** | [Directory Structure.md](./FitSci%20-%20Directory%20Structure.md) | — |
| **What ships in Phase N?** | [Development Plan.md](./FitSci%20-%20Development%20Plan.md) | [Risk Register.md](./FitSci%20-%20Risk%20Register.md), [Cross-Cutting Concerns.md](./FitSci%20-%20Cross-Cutting%20Concerns.md) |
| **What does the Judge actually compute?** | [scoring_basis.md](./scoring_basis.md) | [Research Evaluation Model.md](./FitSci%20-%20Research%20Evaluation%20Model.md), [ADR-0002](./adr/0002-scoring-canonical-spec.md) |
| **Why this Gemma variant?** | [ADR-0004](./adr/0004-gemma4-12b-q4km.md) | [audit-gemma4-selection.md](./audit/before-phase-0/audit-gemma4-selection.md) |
| **Why JSONB and not normalized SQL?** | [ADR-0003](./adr/0003-database-postgres-jsonb.md) | [audit-database.md](./audit/before-phase-0/audit-database.md) |
| **Future Gemma features (post-hackathon)** | [audit-gemma4-features.md](./audit/before-phase-0/audit-gemma4-features.md) | [Development Plan.md §4 Phase 4](./FitSci%20-%20Development%20Plan.md) |
| **Fine-tuning pipeline (post-hackathon)** | [audit-finetuning-pipeline.md](./audit/before-phase-0/audit-finetuning-pipeline.md) | [Development Plan.md §4 Phase 4](./FitSci%20-%20Development%20Plan.md) |
| **Logging / error / cache / metrics ports** | [Cross-Cutting Concerns.md](./FitSci%20-%20Cross-Cutting%20Concerns.md) | [Directory Structure.md](./FitSci%20-%20Directory%20Structure.md) |
| **Prompt-injection defense** | [Cross-Cutting Concerns.md §6](./FitSci%20-%20Cross-Cutting%20Concerns.md) | [Risk Register.md R4](./FitSci%20-%20Risk%20Register.md) |
| **What can go wrong?** | [Risk Register.md](./FitSci%20-%20Risk%20Register.md) | [audit-development-plan.md §4](./audit/before-phase-0/audit-development-plan.md) |
| **Bio-Signal UI aesthetic** | [Design.md](./FitSci%20-%20Design.md) | — |

---

## 7. Document statuses

| Status | Meaning |
|---|---|
| **Active** | Current source of truth for its topic |
| **Canonical for code** | The implementation must agree with this; CI enforces consistency |
| **Locked** | The decision recorded here is not up for re-litigation without a new ADR |
| **Reference / historical** | Preserved for context but not driving current work |
| **Deferred** | Topic exists but is out of scope for v1 (e.g. AuthN/AuthZ, observability traces) |

All current documents are **Active** unless explicitly tagged otherwise in their header.

---

## 8. Doc maintenance rules

* **Pre-commit / CI guards** (Phase 0):
  * Any change to `backend/src/domain/services/scoring.py` must touch `docs/scoring_basis.md` in the same commit ([ADR-0002](./adr/0002-scoring-canonical-spec.md)).
  * Any change to a `domain/ports/*` Protocol should touch [Directory Structure.md](./FitSci%20-%20Directory%20Structure.md) or be accompanied by a new ADR.
  * `INDEX.md` must list every `docs/*.md` file (this file) and every `docs/adr/*.md` file, excluding `internal/`.
* **Audits** in `audit/before-phase-0/` are versioned at the date of the audit and not edited in place; corrections go in a follow-up audit.
* **ADRs** are append-only; supersede with a new ADR.

---

*If you reached here from somewhere unexpected, the canonical pointer to this index is `docs/INDEX.md` from the repo root, or "[Quick links](../README.md#quick-links)" in the README.*
