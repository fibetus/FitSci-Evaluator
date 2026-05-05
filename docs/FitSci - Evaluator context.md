# FitSci Evaluator: Evidence-Based Fitness AI

> **A bridge between complex science and gym practice.** An intelligent system for analyzing and evaluating the credibility of scientific research related to training, nutrition, and hypertrophy.

> **Doc role.** This is the high-level **product context**. For implementation see [`FitSci - Development Plan.md`](./FitSci%20-%20Development%20Plan.md); for architecture see [`FitSci - Technical Architecture.md`](./FitSci%20-%20Technical%20Architecture.md); for everything else see [`INDEX.md`](./INDEX.md).

---

## 1. The Problem (Context)

The fitness industry suffers from a plague of misinformation. Sensational headlines appear every day: *"New study: this supplement increases muscle mass by 50%!"* Unfortunately, most people training lack the competence to critically analyze scientific publications.

**Key problems:**
* **Interpretational errors:** drawing conclusions from beginner-only studies (*noob gains*) that do not translate to advanced trainees.
* **Ignoring statistics:** lack of understanding of statistical significance (*p-value*), sample size (*N*), effect size (*Cohen's d*), and heterogeneity.
* **Information noise:** changing training plans every week under the influence of single, low-quality reports (*Bro-Science*).

## 2. The Solution

**FitSci Evaluator** is an application using **Google Gemma 4** as a personal scientific reviewer. The system automatically analyzes medical and sports publications, extracts structured methodology data, and applies a deterministic scoring engine to deliver a **Credibility Verdict** plus a practical training tip.

Instead of reading 20 pages of medical jargon, the user receives a compact verdict, a bounded **Rigor Index**, and a one-line gym-floor takeaway.

## 3. How it Works (Architecture)

The system follows **Hexagonal Architecture** ([ADR-0001](./adr/0001-architecture-hexagonal.md)). The domain core is pure Python; everything external is an adapter behind a port.

### A. Data extraction (M1 + M2)

* **M1 — Ingestor** fetches paper text (PMC E-utilities adapter; PDF parser via PyMuPDF).
* **M2 — Sifter** is a Gemma 4 adapter that extracts a 30+-field `Study` JSON: study type (meta-analysis, RCT, observational, animal), sample size, training status, *p*-value, effect size, duration, etc.

### B. Scoring algorithm (M3 — The Judge, deterministic)

* **Weight of evidence:** meta-analyses > RCTs > observational > case studies.
* **Beginner / population filter:** flags untrained-only samples; penalizes non-human studies.
* **Effect-size discipline:** rewards reported Cohen's d / 95% CI; treats lone p-values cautiously.
* **Bias gates:** industry funding, missing full text, preprint status feed `bias_pts`.

The current implementation (v1, **0–14 scale**) is documented in [`scoring_basis.md`](./scoring_basis.md). The long-term science target (v2, 0–20, MRI-vs-DEXA, Cohen's d–first) is documented in [`FitSci - Research Evaluation Model.md`](./FitSci%20-%20Research%20Evaluation%20Model.md).

### C. Interpretation layer

* *"High-quality study — consider implementing this technique."*
* *"Small sample size — treat as a curiosity; do not change your plan."*

A future Phase 4 feature ([`audit-gemma4-features.md §2`](./internal/audit/audit-gemma4-features.md)) will fill the `summary_pl` / `summary_en` fields with NTS-style 3-sentence summaries via a 4B Gemma adapter.

## 4. Target Audience

* **Physique sports amateurs** — train smarter, not harder.
* **Personal trainers** — quick knowledge verification + client education.
* **Content creators** — build authority on reliable evidence (Evidence-Based).

## 5. Development Potential (Roadmap)

Tracked in detail in `FitSci - Development Plan.md` Phase 4 and `audit-gemma4-features.md`. Highlights:

- [ ] **PubMed/PMC ingestion adapter** — automatic retrieval of studies (Phase 1).
- [ ] **Lay-Person Translator** (PL/EN, NTS-style) — Phase 4, Gemma 4B.
- [ ] **P-Hacking Sniffer** — Phase 4, Gemma 4B → `IntegrityAuditorPort`.
- [ ] **Study Comparator** — juxtaposing two conflicting publications (Phase 4).
- [ ] **Myth-Buster Search** — claim → studies → verdict (Phase 4).
- [ ] **Citation Triage Assistant** — self-replenishing knowledge base (Phase 4).
- [ ] **Conversational Co-Pilot** ("Ask the Evaluator") — Phase 4, Gemma 12B via Vertex AI streaming.

---

## Technologies (locked — see [adr/](./adr/README.md))

| Layer | Choice |
|---|---|
| Language model | **Google Gemma 4** — 12B Q4_K_M (production) / 4B Q4_K_M (CI/dev) |
| LLM runtime | **Ollama** locally and for CI; **Vertex AI Model Garden** in production |
| Backend | **Python + FastAPI + Pydantic v2** |
| Architecture | **Hexagonal (Ports & Adapters)** |
| Database | **PostgreSQL 16+** with **JSONB-first** schema; `pgvector` reserved for v2 |
| Frontend | **React (Vite + TypeScript)** with Bio-Signal aesthetic ([`Design.md`](./FitSci%20-%20Design.md)) |
| API contract | OpenAPI 3 → `openapi-typescript` codegen committed to the frontend repo |
| Migrations | Alembic |

> **Out of scope for v1:** Retrieval-Augmented Generation (RAG), vector search, multi-tenant auth, real-time streaming. The system *evaluates* papers; it does not retrieve from them.

---

## Development Resources

Start at **[`docs/INDEX.md`](./INDEX.md)** for the full navigation map.

* **Master plan:** [`FitSci - Development Plan.md`](./FitSci%20-%20Development%20Plan.md)
* **Architecture:** [`FitSci - Technical Architecture.md`](./FitSci%20-%20Technical%20Architecture.md), [`FitSci - Directory Structure.md`](./FitSci%20-%20Directory%20Structure.md)
* **Decisions:** [`adr/`](./adr/README.md)

---

*Project created for the Kaggle hackathon: Gemma 4 Good.*
