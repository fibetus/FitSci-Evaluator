# FitSci - Stack Analysis & Path Forward

This document evaluates the technological path for **FitSci - Evaluator**, comparing the current MVP stack against a Python-centric alternative.

---

## 1. Frontend Comparison: React vs. Streamlit

| Feature | Current React Frontend (Vite) | Streamlit |
| :--- | :--- | :--- |
| **Visual Quality** | **Elite.** Custom "Bio-Signal" aesthetic, CRT effects, neon glows. | **Standard.** Functional "Data Science" look. Hard to achieve the "Bio-Signal" vibe. |
| **Interactivity** | High. Smooth animations (Framer Motion), complex grids, radial gauges. | Moderate. Layout is mostly linear/column-based. Limited custom components. |
| **Dev Speed** | Slow. Requires manual state management and UI styling. | **Fast.** Write UI in pure Python. No HTML/CSS knowledge needed. |
| **Hackathon Impact** | **High.** Judges are impressed by polished, unique custom UIs. | **Moderate.** Clearly looks like a prototype. High focus on logic, less on "feel." |

**Verdict:** Since you already have the React code and **love the aesthetic**, switching to Streamlit would be a "downgrade" in terms of hackathon presentation (Gemma 4 Good rewards impact and vision).

---

## 2. Backend Analysis: Python (FastAPI)

**Decision: Rewriting the Backend in Python makes 100% sense.**
*   **AI Ecosystem:** Most Gemma 4 libraries (Kaggle Hub, Transformers, LangChain) are Python-native.
*   **Integration:** Your existing scraper is already in Python. Unifying them into a single FastAPI app simplifies the architecture.
*   **Speed:** FastAPI is nearly as fast as Node.js and much easier for AI workflows.

---

## 3. The Better Path: The Hybrid "Power" Stack

Instead of merging everything into one language, we should use a **Headless Architecture**.

### Proposed Stack
*   **Backend:** **Python (FastAPI)**. Handles Gemma 4 inference, scoring logic, and the scraping pipeline.
*   **Frontend:** **Existing React (Vite)**. Kept as a separate application that communicates with the Python API via JSON.
*   **Database:** **PostgreSQL** (already used in your MVP).

### Why this path?
1.  **Don't throw away the gold:** Your current UI is a major asset for a hackathon.
2.  **Logic where it belongs:** Python is the industry standard for LLM orchestration.
3.  **Scalability:** If you need to switch from local Gemma (Ollama) to cloud Gemma (Vertex AI), Python makes it a 5-line change.

---

## 4. Proposed Development Roadmap: CLI-to-UI

To manage complexity, we will follow this "Inside-Out" strategy:

### Phase 1: The Core "Scientist" (CLI)
*   Build the FastAPI backend first.
*   Create a simple **CLI tool** in Python to test the scraper -> Gemma 4 -> Scoring Matrix flow.
*   Output results to the terminal in clean JSON.
*   *Goal: Ensure the "Credibility Verdict" logic is flawless.*

### Phase 2: The Bridge (API)
*   Expose the Python logic through FastAPI endpoints (`/api/studies`, `/api/evaluate`).
*   Ensure the JSON output matches the **Bio-Signal UI** requirements (the `Study` type).

### Phase 3: The "Bio-Signal" UI (Frontend)
*   Reconnect the React frontend to the new Python API.
*   Fix any data-type mismatches.
*   Add final polish (animations, loading states).

---

## Conclusion
**Do not use Streamlit.** It will kill the unique visual identity you've built. Instead, **rewrite the backend in FastAPI** and keep your **React frontend**. This gives you the best of both worlds: Scientific power and Visual impact.

---
*Next Action: Update [[FitSci - Development Plan]] to reflect the FastAPI + React stack.*
