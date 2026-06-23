# FitSci - Technical Architecture Specification

> **Status (2026-05-06):** **Decision locked — Option A (Hexagonal) chosen.** This document is preserved for historical context (the three options that were on the table) and as a quick reference to *why* hexagonal won. The authoritative ADR is [`adr/0001-architecture-hexagonal.md`](../adr/0001-architecture-hexagonal.md). For the implementation layout, see [`FitSci - Directory Structure.md`](./FitSci%20-%20Directory%20Structure.md).

The goal of FitSci is a **highly decoupled, modular system** where individual components (Scraper, Evaluator, API) operate independently — including a "Plug-and-Play" Sifter that can ingest raw text directly, bypassing the Scraper.

---

## 1. Architectural Options (historical comparison)

> **Decision:** **Option A — Hexagonal (Ports & Adapters).** Rationale and trade-offs in [ADR-0001](../adr/0001-architecture-hexagonal.md). Options B and C are kept here as honest documentation of the alternatives considered.

### Option A: Hexagonal (Ports & Adapters)  ✅ **CHOSEN**

* **Concept:** the "Core" contains business logic (Scoring Matrix). External systems (Gemma 4, Scrapers, DB, UI) are **Adapters** that plug into **Ports**.
* **Independence strategy:** M2 (Evaluator) is a standalone Port — feed it a JSON string or a PDF stream; it returns a Pydantic object to the Core.
* **Pros:**
  * **Ultimate decoupling.** Swap LLMs, databases, frontends with zero impact on core logic.
  * **Testability.** The Judge (Scoring) is testable without internet, AI, or DB.
  * **Survives the Phase 4 fine-tuning track.** A fine-tuned Gemma adapter is a constructor swap, not a refactor (see [`audit-finetuning-pipeline.md §4`](../audit/before-phase-0/audit-finetuning-pipeline.md)).
* **Cons:** higher initial setup time; requires strict interface definitions.

### Option B: Clean Layered (Standard Enterprise)

* **Concept:** strict vertical layers `API → Service → Repository`.
* **Pros:** high velocity; familiar pattern.
* **Cons:** layers tend to couple over time; "swap LLM in 5 lines" is much harder once service layer references SDK types.
* **Why rejected:** does not preserve the explicit "5-line swap" promise from [`Stack Analysis §3`](../stack/FitSci%20-%20Stack%20Analysis.md).

### Option C: Modular Monolith

* **Concept:** modules separated by folder/namespace; communicate via internal Command/Event objects.
* **Pros:** extreme isolation, easy future extraction to microservices.
* **Cons:** complex internal communication; overkill for a hackathon-scale codebase.
* **Why rejected:** the team is one or two contributors; the cost of Command/Event plumbing is not earned at this size.

---

## 2. Decoupling the Pipeline (the "Direct-to-Gemma" path)

The chosen architecture supports two execution flows:

1. **Standard path:** `Ingestor (M1) → Sifter (M2) → Judge (M3) → Vault (M4)`.
2. **Evaluation-only path:** `User/CLI input → Sifter (M2) → Judge (M3) → Display`.

Both flows are realized by the **application layer** (`backend/src/application/use_cases/`) — see [`audit-architecture.md §4.2`](../audit/before-phase-0/audit-architecture.md). Adapters are constructed at the composition root (`cli/main.py` for the CLI, `main.py` for FastAPI) and injected into the use cases.

---

## 3. Comparison Recap

| Feature | Hexagonal (chosen) | Clean Layered | Modular Monolith |
| :--- | :--- | :--- | :--- |
| **Vulnerability resistance** | High (isolated ports) | Moderate | Highest (process isolation) |
| **Ease of maintenance** | High (loose coupling) | Moderate | High (clear boundaries) |
| **Gemma 4 integration** | **Best** (adapter pattern) | Good | Good |
| **CLI implementation** | Easy | Easy | Best (separate entrypoints) |
| **5-line LLM swap** | **Yes** | No | Yes |
| **Fits hackathon timeline** | Yes (after Phase 0 scaffold) | Yes | Risky (ceremony cost) |

---

## 4. Implementation pointers

* **Ports (interfaces) live in `backend/src/domain/ports/`.** Use `typing.Protocol` (structural typing) — the lightest possible contract.
* **Adapters (implementations) live in `backend/src/adapters/<area>/`.** Adapters are the only modules permitted to import third-party infra (HTTP clients, DB drivers, LLM SDKs).
* **Use cases live in `backend/src/application/use_cases/`** and orchestrate ports for one user-facing operation.
* **Composition roots are `cli/main.py` and `main.py` (FastAPI).** They construct adapters and inject them into use cases.
* **Pydantic is the one third-party dependency permitted in `domain/`** (see [ADR-0001](../adr/0001-architecture-hexagonal.md) for the explicit exception).

---

## 5. Where to read more

| If you want to know... | Read |
|---|---|
| Why hexagonal won, and what alternatives were considered | [`adr/0001-architecture-hexagonal.md`](../adr/0001-architecture-hexagonal.md) |
| How the directory tree maps to ports and adapters | [`FitSci - Directory Structure.md`](./FitSci%20-%20Directory%20Structure.md) |
| What gets built in which phase, and how DoD is measured | [`FitSci - Development Plan.md`](./FitSci%20-%20Development%20Plan.md) |
| How LLM provider swap actually works (Ollama ↔ Vertex AI) | [`adr/0004-gemma4-12b-q4km.md`](../adr/0004-gemma4-12b-q4km.md) and [`audit-gemma4-selection.md`](../audit/before-phase-0/audit-gemma4-selection.md) |
| What database choices look like behind the port | [`adr/0003-database-postgres-jsonb.md`](../adr/0003-database-postgres-jsonb.md) and [`audit-database.md`](../audit/before-phase-0/audit-database.md) |
| The deep architecture audit | [`audit-architecture.md`](../audit/before-phase-0/audit-architecture.md) |

---

*Status: Hexagonal locked. Phase 0 of the [Development Plan](./FitSci%20-%20Development%20Plan.md) operationalizes the missing pieces (application layer, ports for logger/clock, error taxonomy, ADRs).*
