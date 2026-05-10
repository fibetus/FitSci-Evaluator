# FitSci Evaluator — Full Project Audit (Index)

**Date:** 2026-05-02
**Last reviewed by:** Claude Opus (automated audit)
**TL;DR:** Vision and architectural choice are excellent; documentation is thorough; spec-vs-code drift and missing cross-cutting concerns are the dominant risks. Overall project health: **6.5 / 10**.

---

## Executive Summary (≤500 words)

FitSci - Evaluator is an evidence-based fitness AI that ingests sport-science publications, extracts structured methodology data using Gemma 4, and emits a "Credibility Verdict" computed by a deterministic scoring engine. The vision is unusually clear, the source material (`Badania naukowe w treningu siłowym: interpretacja`) is genuinely substantive, and the chosen architecture (Hexagonal / Ports & Adapters with FastAPI backend + React frontend) is a deliberate, well-justified choice rather than a default. The team has already produced eight orthogonal `/docs` files covering vision, design, plan, structure, stack, models, technical architecture, and engineering guidelines — a level of documentation discipline ahead of most hackathon projects.

That said, the audit surfaces several material problems:

1. **⛔ Spec/code drift on the scoring engine.** The "Rigor Index" is documented as a 0–20 scale grounded in MRI/DEXA, Cohen's d, and trained-vs-untrained criteria from the source PDF. The actual `backend/src/domain/services/scoring.py` implements a different ~14-point scale based on study type, sample size, recency, impact factor, and bias flags — and references a `GEMINI.md` file that does not exist in `/docs`. Whoever joins next will either build against the wrong spec or against an invisible one. (See `audit-architecture.md` §3 Blocker 1.)
2. **⛔ README contradicts the rest of `/docs`.** It still lists Streamlit, LangChain, and LlamaIndex — exactly the choices that `FitSci - Stack Analysis.md` explicitly rejects in favor of FastAPI + React. (`audit-architecture.md` §3 Blocker 2.)
3. **No application/use-case layer.** The CLI directly orchestrates domain services with hardcoded mock data, mixing the role of an entrypoint with that of a use-case orchestrator. This will get worse, not better, when FastAPI controllers arrive in Phase 2. (`audit-architecture.md` §3.)
4. **Cross-cutting concerns are absent from the development plan.** Auth, logging, observability, error taxonomy, prompt-injection mitigation, rate-limiting, caching, secrets management, CI/CD — none are addressed. The plan is strategically correct but tactically thin. (`audit-development-plan.md` §3.)
5. **Frontend type drift is unguarded.** Phase 3 hand-syncs TypeScript types against a 30+ field Pydantic model. Without OpenAPI codegen, drift is guaranteed. (`audit-development-plan.md` §3.)

The recommendations are not radical: pick one canonical scoring spec and write it as an ADR, rewrite the README, add an application layer, codegen TypeScript types, and add a Phase 0 (foundation) before continuing implementation. The hexagonal investment already paid for makes every other proposed change — including the long-term fine-tuning pipeline (`audit-finetuning-pipeline.md`) — a constructor-argument swap rather than a refactor.

Database choice: keep PostgreSQL but use it as a JSONB-first document store with GIN indexes and `pgvector` as a future extension; avoid the canonical "Study inherits from SQLModel" trap. Gemma sizing: 12B Q4_K_M for production extraction, 4B for CI and most ancillary features (translation, p-hacking sniffer, comparator), with a 27B-or-fine-tune escalation path defined quantitatively rather than by feel.

The single highest-leverage change is **resolving the scoring-spec drift before any further code is written**. Everything else is much cheaper to fix afterward.

---

## Audit Documents

1. [Architecture audit](./audit-architecture.md) — hexagonal layers, ports, adapters, anti-patterns, immediate fixes.
2. [Development plan audit](./audit-development-plan.md) — phase analysis, gap analysis, top-5 risks, recommended amendments.
3. [Database audit](./audit-database.md) — PostgreSQL JSONB recommendation, repository port design, anti-patterns.
4. [Gemma 4 selection audit](./audit-gemma4-selection.md) — variant + quantization + deployment + upgrade thresholds.
5. [Gemma 4 feature extensions audit](./audit-gemma4-features.md) — six concrete features, per-feature variant sizing.
6. [Fine-tuning pipeline audit](./audit-finetuning-pipeline.md) — Hermes scrape → Opus 4 evaluation → QLoRA on Gemma 4 12B → A/B-tested deployment behind one port.

---

## Project Health Score: **6.5 / 10**

### Score breakdown

| Dimension | Score (0–10) | Justification |
|---|---|---|
| Vision & problem framing | 9 | Clear, well-grounded in cited research; differentiated from generic "AI fitness" projects |
| Documentation breadth | 8 | 8 substantive markdown files + a 29-page methodology source PDF, all with consistent voice |
| Documentation consistency | 4 | README contradicts Stack Analysis; Research Evaluation Model contradicts code; missing `GEMINI.md` is referenced from code |
| Architectural choice | 9 | Hexagonal is correctly chosen and justified for an LLM-pipeline project with explicit "swap Gemma 4 for Vertex AI in 5 lines" requirement |
| Architectural execution | 6 | Ports correctly defined; adapters not yet built; no application layer; anemic domain model; `Study.flags: dict` is untyped |
| Phase planning | 7 | Inside-out CLI→API→UI ordering is right; phases lack DoD richness, time-boxes, and explicit cross-cutting concerns |
| Risk awareness | 4 | No documented risk register; no prompt-injection plan beyond "sanitize"; no observability or auth strategy |
| Tech stack fit | 8 | FastAPI + Pydantic + Ollama + PostgreSQL is well-matched to the workload; Vertex AI escalation is sane |
| Frontend integration plan | 5 | Hexagonal isolation is correct; type-drift safeguards (codegen, schema versioning) are absent |
| Code quality where present | 7 | Tests exist for the implemented scoring service; ports use Protocol; clean layering — but spec drift undermines this |
| **Overall** | **6.5** | Excellent vision and architectural intent, undermined by spec/doc drift and missing cross-cutting concerns. The fixes are small. |

### What would move it to 8+
- Resolve the scoring spec drift; one canonical ADR.
- Rewrite the README to match the rest of `/docs`.
- Add an application/use-case layer.
- Add an `/docs/adr/` folder with ADRs 0001–0004.
- Add OpenAPI → TypeScript codegen.
- Add a logger port, clock port, and error taxonomy in `domain/`.
- Add Definitions of Done with measurable acceptance criteria for each phase.

### What would move it to 9+
- Implement Phase 1 end-to-end with no mocks (real PMC fetch + real Gemma call + real schema-validated output) on at least 5 benchmark studies.
- Ship the Phase 4 fine-tuning pipeline behind the routing adapter described in `audit-finetuning-pipeline.md` §4, with telemetry, rollback levers, and a versioned canary deploy.
- Adopt the cross-cutting concerns checklist (auth, logging, observability, prompt-injection, caching, rate-limiting) as gated milestones rather than future-work bullets.

---

*End of audit index.*
