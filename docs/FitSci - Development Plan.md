# FitSci - Evaluator: Master Development Plan

This document serves as the definitive implementation roadmap for the **FitSci - Evaluator** project for the **Gemma 4 Good Hackathon**. It integrates the **Hexagonal Architecture**, the **Hybrid Stack**, and the **"Bio-Signal" Design** into a single, cohesive execution strategy.

---

## 1. Vision & Strategy
**FitSci** bridges the gap between sports science and gym practice. We use **Gemma 4** to sift through the noise of scientific publications, applying a rigorous, automated scoring engine to deliver a "Credibility Verdict."

### Strategy: CLI-to-UI (Inside-Out)
We will build and verify the "Science Core" in a headless environment first. This ensures our AI extraction and scoring logic is flawless before we connect the complex React frontend.

---

## 2. Technical Stack
*   **Backend (The Science):** Python (FastAPI).
*   **Frontend (The Signal):** React (Vite + TypeScript + Framer Motion).
*   **AI Engine:** Google Gemma 4 (Local via Ollama for dev; Vertex AI for production).
*   **Database:** PostgreSQL (Metadata-only).
*   **Architecture:** Hexagonal (Ports & Adapters).

---

## 3. Module Breakdown & Implementation Details

### M1: The Ingestor (Scrapers & Parsers)
*   **Responsibility:** Fetching raw text.
*   **Port:** `IngestorPort` (Abstract class with `fetch_by_id` and `search` methods).
*   **Adapters:** 
    *   `PMCAdapter`: Fetches full text from PMC E-utilities.
    *   `PDFAdapter`: Local file parser (using `PyMuPDF`).
*   **Validation:** Can retrieve a known study by ID and return clean text.

### M2: The Sifter (Gemma 4 Evaluator)
*   **Responsibility:** LLM-driven structured data extraction.
*   **Port:** `EvaluatorPort` (Abstract class with `evaluate_text` method).
*   **Adapter:** `GemmaAdapter` (Prompt-engineered interface to Gemma 4).
*   **Details:** Uses Pydantic models to force Gemma into the `Scientist Scraper` JSON schema ($N$, $p$-value, $d$, study type).
*   **Validation:** Reproduce consistent JSON output from a set of 5 "Benchmark" studies.

### M3: The Judge (Domain Core)
*   **Responsibility:** Business logic and scoring.
*   **Implementation:** Pure Python (no external dependencies).
*   **Logic:**
    *   **Rigor Index:** Calculates 0–20 score (MRI vs. DEXA, Trained vs. Untrained).
    *   **Integrity Filter:** Detects p-hacking signs and funding bias.
    *   **APEASE Matrix:** Maps findings to practical utility.
*   **Validation:** Unit tests with mock metadata covering all score permutations.

### M4: The Vault (Storage & API)
*   **Responsibility:** Persistence and UI serving.
*   **Port:** `RepositoryPort`.
*   **Adapter:** `SQLModelAdapter` (PostgreSQL).
*   **Logic:** Implements the **"Extract & Discard"** pattern. Only saves the evaluation JSON, not the raw text.
*   **Validation:** Database migrations (Alembic) and CRUD verification.

---

## 4. Phased Implementation Roadmap

### Phase 1: The Core "Scientist" (CLI MVP)
1.  **Define Domain Models:** Create Pydantic schemas for `Study`, `Evaluation`, and `ScoringResult`.
2.  **Implement The Judge (M3):** Code the Rigor Index and APEASE logic. **Verify with Unit Tests.**
3.  **Implement The Sifter (M2):** Build the `GemmaAdapter`. Tune prompts for accurate extraction.
4.  **CLI Entrypoint:** Create `cli/main.py` that takes a PMCID, runs M1 -> M2 -> M3, and prints a colored JSON report to the terminal.
*   **SUCCESS:** A command like `python -m fitsci eval PMC12345` prints a valid "Credibility Verdict."

### Phase 2: The "Bio-Signal" Bridge (API Integration)
1.  **FastAPI Setup:** Initialize the web server and Dependency Injection (DI) container.
2.  **Implement The Vault (M4):** Set up PostgreSQL and SQLModel adapters.
3.  **API Endpoints:**
    *   `GET /studies`: List all evaluations.
    *   `POST /evaluate`: Trigger evaluation of a new study/URL.
    *   `GET /studies/{id}`: Detail view for the React UI.
*   **SUCCESS:** Swagger UI (`/docs`) allows triggering and viewing evaluations.

### Phase 3: The Dashboard (Frontend Reconnect)
1.  **Data Alignment:** Update the existing React `Study` type to match the Python Pydantic models.
2.  **API Connection:** Swap mock data in the frontend for live FastAPI calls.
3.  **Visual Polish:** Finalize the "Bio-Signal" aesthetic (CRT effects, Confidence Gauges) based on real scores.
*   **SUCCESS:** The React dashboard displays live evaluations from the Python backend.

---

## 5. Security & Maintenance Guidelines (CLAUDE.md)
*   **Surgical Changes:** When migrating from the old MVP, touch only the logic needed. Match the existing "Bio-Signal" style exactly.
*   **Simplicity First:** Avoid complex AI agent frameworks (like CrewAI/LangGraph) if simple prompt-chaining in M2 suffices.
*   **Input Sanitization:** Sanitize all text before sending to Gemma 4 to prevent prompt injection.
*   **Dependency Injection:** Always use DI for Adapters to ensure M2 and M4 can be mocked in tests.

---
*Status: READY FOR IMPLEMENTATION*
*Next Step: Initialize Phase 1 - Domain Models.*
