# FitSci - Technical Architecture Specification

This document defines the structural blueprint for the **FitSci - Evaluator**. The goal is a **highly decoupled, modular system** where individual components (Scraper, Evaluator, API) can operate independently.

---

## 1. Architectural Options

We propose three distinct architectural models. Each supports the "Plug-and-Play" requirement: the ability to feed raw text directly into the Evaluator (M2) bypassing the Scraper (M1).

### Option A: Hexagonal (Ports & Adapters)
*   **Concept:** The "Core" contains the business logic (Scoring Matrix). External systems (Gemma 4, Scrapers, DB, UI) are "Adapters" that plug into "Ports."
*   **Independence Strategy:** M2 (Evaluator) is a standalone "Port." You can feed it a JSON string or a PDF stream; it simply extracts data and returns a Pydantic object to the Core.
*   **Pros:** 
    *   **Ultimate Decoupling:** You can swap LLMs or Databases with zero impact on core logic.
    *   **Testability:** You can test the "Judge" (Scoring) without even having an internet connection or an AI model.
*   **Cons:** Higher initial setup time; requires strict interface definitions.

### Option B: Clean Layered (Standard Enterprise)
*   **Concept:** Strict vertical layers: `API` -> `Service` -> `Repository`.
*   **Independence Strategy:** The `EvaluationService` is public. The `ScraperService` is also public. You can call `EvaluationService.evaluate(text)` from any entry point (CLI or API) without touching the scraper.
*   **Pros:** 
    *   **High Velocity:** Very fast to implement in FastAPI.
    *   **Familiarity:** Most developers understand this pattern immediately.
*   **Cons:** Tendency for layers to become coupled over time if not strictly monitored.

### Option C: Modular Monolith (The "Micro-Service" Simulation)
*   **Concept:** Modules are strictly separated by folder/namespace and communicate only via internal "Command" or "Event" objects.
*   **Independence Strategy:** M1, M2, and M3 are treated as separate "packages" inside the same repo. M2 has its own `main.py` entry point for CLI use.
*   **Pros:** 
    *   **Extreme Isolation:** A bug in the Scraper cannot possibly crash the Evaluator.
    *   **Scalability:** If the AI Evaluator needs more RAM, you can easily pull that folder out into a separate server later.
*   **Cons:** Complex communication; might feel "heavy" for a hackathon project.

---

## 2. Decoupling the Pipeline (The "Direct-to-Gemma" Path)

Regardless of the choice, the architecture will support the following **Execution Flow**:

1.  **Standard Path:** `Ingestor (M1)` -> `Sifter (M2)` -> `Judge (M3)` -> `Vault (M4)`.
2.  **Evaluation-Only Path:** `User/CLI Input` -> `Sifter (M2)` -> `Judge (M3)` -> `Display`.

---

## 3. Security & Maintenance Comparison

| Feature | Hexagonal | Clean Layered | Modular Monolith |
| :--- | :--- | :--- | :--- |
| **Vulnerability Resistance** | High (Isolated Ports) | Moderate | **Highest (Process Isolation)** |
| **Ease of Maintenance** | High (Loose Coupling) | Moderate | High (Clear Boundaries) |
| **Gemma 4 Integration** | **Best** (Adapter pattern) | Good | Good |
| **CLI Implementation** | Easy | Easy | **Best** (Separate Entrypoints) |

---

## 4. Final Comparison for Hackathon

| Option | Recommendation |
| :--- | :--- |
| **Hexagonal** | **Choose if** you want a "production-ready" architecture that showcases elite engineering to the judges. |
| **Clean Layered** | **Choose if** time is the primary constraint and you want to finish the MVP as fast as possible. |
| **Modular Monolith** | **Choose if** you plan to expand this into a huge multi-agent system after the hackathon. |

---
*Next Step: Please select Option A, B, or C to proceed with Task Generation.*
