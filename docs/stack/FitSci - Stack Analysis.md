# FitSci - Stack Analysis & Path Forward

> **Status (2026-05-06):** **Verdict locked — Hybrid stack chosen: Python (FastAPI) backend + React (Vite) frontend.** This document is preserved for the side-by-side comparison that produced the decision. The authoritative ADR is [`adr/0001-architecture-hexagonal.md`](../adr/0001-architecture-hexagonal.md). **Streamlit / Gradio / LangChain / LlamaIndex are explicitly out — do not reintroduce them.**

This document evaluates the technological path for **FitSci - Evaluator**, comparing the prior MVP stack against the chosen Python-centric alternative.

---

## 1. Frontend Comparison: React vs. Streamlit

| Feature | React Frontend (Vite) — **chosen** | Streamlit |
| :--- | :--- | :--- |
| **Visual quality** | **Elite.** Custom Bio-Signal aesthetic, CRT effects, neon glows. | Standard "data science" look; Bio-Signal vibe is impractical. |
| **Interactivity** | High. Smooth animations (Framer Motion), complex grids, radial gauges. | Moderate. Mostly linear/column layouts; limited custom components. |
| **Dev speed** | Slow (manual state + styling). | Fast (Python-only UI). |
| **Hackathon impact** | **High.** Judges respond to polished, distinctive UIs. | Moderate. Reads as a prototype. |

**Verdict:** since the React Bio-Signal codebase already exists and is the project's strongest visual asset, switching to Streamlit would be a downgrade for *Gemma 4 Good* presentation. **React stays.**

---

## 2. Backend: Python (FastAPI) — chosen

* **AI ecosystem:** the entire Gemma 4 toolchain (Kaggle Hub, Transformers, Ollama, Vertex AI Python SDK) is Python-native.
* **Integration:** the ingestor is Python; unifying behind one FastAPI app keeps the stack coherent.
* **Speed:** FastAPI is fast enough; AI workflows benefit far more from Python ergonomics than from Node throughput.
* **OpenAPI for free:** FastAPI emits OpenAPI 3 out of the box, which we feed into `openapi-typescript` for the React frontend (kills hand-synced type drift — see [`audit-architecture.md §4.3`](../audit/before-phase-0/audit-architecture.md)).

---

## 3. The Better Path: the Hybrid "Power" Stack — **chosen**

A **headless architecture**:

* **Backend:** Python (FastAPI). Gemma 4 inference, scoring, scraping pipeline.
* **Frontend:** React (Vite). Communicates with the Python API via JSON; types are codegen'd from `/openapi.json`.
* **Database:** PostgreSQL with JSONB-first schema. See [`adr/0003-database-postgres-jsonb.md`](../adr/0003-database-postgres-jsonb.md).

### Why this path

1. **Don't throw away the gold.** The Bio-Signal UI is a major hackathon asset.
2. **Logic where it belongs.** Python is the industry standard for LLM orchestration.
3. **The 5-line LLM swap is real.** Switching from local Gemma (Ollama) to cloud Gemma (Vertex AI) means swapping `GemmaOllamaAdapter` for `GemmaVertexAIAdapter` in the composition root — see [`audit-gemma4-selection.md §3`](../audit/before-phase-0/audit-gemma4-selection.md).

---

## 4. Roadmap recap (Inside-Out / CLI-to-UI)

The phased plan below is summarized; the authoritative version (with measurable Definitions of Done, time-boxes, cross-cutting concerns, and a risk register) lives in [`FitSci - Development Plan.md`](../architecture/FitSci%20-%20Development%20Plan.md).

### Phase 0 — Foundation (1 day)
ADRs, doc reconciliation, application layer skeleton, `LoggerPort`/`ClockPort`, error taxonomy, CI bootstrap.

### Phase 1 — Core Scientist (CLI MVP, 3 days)
Real `PMCAdapter` + real `GemmaOllamaAdapter` + benchmark fixtures. **No mock data.** Output validates against `Study` Pydantic schema; M2 ≥80% field-level F1 on 5 fixtures; M3 ≥90% line coverage.

### Phase 2 — Bridge (FastAPI + persistence, 2 days)
`/api/v1/` versioned endpoints; `POST /evaluate` returns 202 + job ID; idempotency on duplicate PMCID; OpenAPI snapshot committed; rate-limit + correlation IDs.

**Schema-freeze gate** between Phase 2 and Phase 3 — the `Study` schema becomes the immutable v1 contract.

### Phase 3 — Bio-Signal Dashboard (React migration, 2 days)
Codegen'd types from `/openapi.json`; mocks replaced with live calls; loading/empty/error states implemented; visual parity with the legacy app.

### Phase 4 — Fine-tuning + Feature Extensions (post-hackathon, 2–4 weeks)
Gemma 4 12B QLoRA on a 5–10k curated dataset, deployed behind a `RoutingEvaluatorAdapter` for canary rollout. Six Gemma feature extensions (lay translator, p-hacking sniffer, comparator, myth-buster, citation triage, co-pilot). Full design in [`audit-finetuning-pipeline.md`](../audit/before-phase-0/audit-finetuning-pipeline.md) and [`audit-gemma4-features.md`](../audit/before-phase-0/audit-gemma4-features.md).

---

## Conclusion

* **Streamlit is out.** It would kill the Bio-Signal identity.
* **The backend is FastAPI + Pydantic.** Hexagonal architecture isolates Gemma, the database, and the UI.
* **The frontend is the existing React (Vite) Bio-Signal app**, fed by a codegen'd typed client.
* **No agent frameworks.** Plain prompt-chaining inside `adapters/ai/` until a workload demonstrably needs more.

This gives us: scientific power + visual impact + maintainable seams.

---

*Companion documents: [`FitSci - Development Plan.md`](../architecture/FitSci%20-%20Development%20Plan.md) · [`FitSci - Technical Architecture.md`](../architecture/FitSci%20-%20Technical%20Architecture.md) · [`adr/`](../adr/README.md).*
