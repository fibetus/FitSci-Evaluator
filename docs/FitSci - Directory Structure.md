# FitSci - Hexagonal Project Structure

Based on the choice of **Option A: Hexagonal Architecture**, the project directory will be organized to separate business logic from external dependencies.

```text
fitsci-evaluator/
├── backend/                # Python (FastAPI) Backend
│   ├── src/
│   │   ├── domain/         # CORE: Business Logic (Pure Python, No external deps)
│   │   │   ├── models/     # Pydantic schemas (Study, Evaluation, Scoring)
│   │   │   ├── services/   # Scoring Engine logic (Rigor Index, APEASE)
│   │   │   └── ports/      # Abstract Interfaces (Protocols)
│   │   │       ├── ingestor.py
│   │   │       ├── evaluator.py
│   │   │       └── repository.py
│   │   │
│   │   ├── adapters/       # EXTERNAL: Implementation of Ports
│   │   │   ├── ai/         # Gemma 4 / Ollama adapter
│   │   │   ├── scrapers/   # PMC / PubMed scrapers
│   │   │   ├── db/         # PostgreSQL / SQLModel adapter
│   │   │   └── api/        # FastAPI routes & controllers
│   │   │
│   │   ├── cli/            # CLI Entrypoint for Phase 1
│   │   │   └── main.py
│   │   │
│   │   └── main.py         # FastAPI Entrypoint
│   │
│   ├── tests/              # Unit & Integration tests
│   ├── .env                # API Keys (Gemma, NCBI)
│   └── pyproject.toml      # Dependency management (Poetry/Pip)
│
├── frontend/               # React (Vite + TypeScript)
│   ├── src/                # Existing "Bio-Signal" UI code
│   └── ...
│
└── docs/                   # Obsidian Documentation (Linked)
```

---

## 1. How Modularity Works in this Structure

*   **Replacing Gemma 4:** If you want to switch from `adapters/ai/ollama.py` to `adapters/ai/vertex_ai.py`, you only change the adapter. The `domain/services/` never notice the change because they only talk to the `evaluator.py` port.
*   **CLI-First Development:** You can build `backend/src/cli/main.py` to call the `domain` logic directly. It works exactly like the API will later, but without the web overhead.
*   **Direct-to-Gemma Path:** The CLI can instantiate the `GemmaAdapter` and call the `ScoringService` without ever touching the `scrapers/` folder.

---

## 2. Next Step: Implementation Tasks
Shall I generate the first set of implementation tasks (e.g., defining the Domain Models and Ports) to start the **Phase 1: CLI MVP**?
