# Phase 1 Summary: The Core "Scientist" (CLI MVP)

## Overview

Phase 1 establishes the core pipeline of FitSci-Evaluator: fetching real scientific papers, extracting structured data via a Large Language Model, and scoring them using a deterministic ruleset. The overarching goal was to replace all mock data with a real, functioning Hexagonal Architecture pipeline triggered from a simple CLI.

## Completed Work

1. **Ingestor Implementation (`PMCAdapter`)**:
   - Designed to fetch XML directly from NCBI E-utilities.
   - Built with local file-system caching (`~/.fitsci/cache/pmc/`) to prevent repeated expensive network calls and IP bans.
2. **Evaluator Implementation (`GemmaOllamaAdapter`)**:
   - Connects to local Ollama (`gemma4:12b-q4_k_m`) to process the raw paper text.
   - Outputs a highly structured 30-field JSON mapping directly to our `Study` Pydantic model.
   - Employs a robust retry loop: if JSON parsing or Pydantic validation fails, it feeds the validation error back to Gemma for self-correction.
3. **Use Case Orchestration (`EvaluateStudyUseCase`)**:
   - Wires together the `IngestorPort`, `EvaluatorPort`, `RepositoryPort`, and `ScoringService`.
   - Incorporates `ClockPort` and `LoggerPort` for auditable execution and error boundaries based on the unified domain error taxonomy.
4. **CLI Rewrite**:
   - `cli/main.py` is now a true composition root that injects dependencies (including the new `InMemoryStudyRepository` and `ConsoleLogger`).
   - Hardcoded mock data has been cleanly sequestered behind a `--mock` flag.
5. **Extraction Accuracy Harness**:
   - Implemented a `pytest` job (`backend/tests/benchmark/test_extraction_accuracy.py`) using 5 hand-curated JSON benchmark fixtures.
   - Developed a custom flattened F1 structural metric (documented in [ADR-0005](./adr/0005-extraction-accuracy-f1-metric.md)) to reliably test the LLM's accuracy without artificially penalizing it for list reordering or partial matches.

## Definition of Done (DoD) Verification

- [x] **Real Ingestor & Gemma**: The CLI connects to real NCBI APIs and real local Ollama.
- [x] **No hardcoded mock dependencies**: The standard CLI path (`python -m src.cli.main PMC12345`) uses exclusively real ports and adapters.
- [x] **Benchmark fixtures**: 5 PMC IDs with curated JSON structures are saved and version-controlled.
- [x] **F1 Accuracy Test**: The pytest job verifies field-level F1 >= 80%.
- [x] **Documentation up-to-date**: ADRs created, `Development Plan` updated, `README` reflects real status.

## How to Test Offline (Without Ollama)

Since running the full AI pipeline requires downloading a 12B parameter model and spinning up Ollama, you can verify the structure and CLI operation completely offline:

1. **Test the CLI Offline (Mock Mode)**:
   ```bash
   cd backend
   python -m src.cli.main --mock PMC12345
   ```
   This uses the legacy mock data to prove the CLI prints the expected Credibility Verdict layout and calculates the score correctly without hitting the network.

2. **Run Standard Unit Tests**:
   ```bash
   cd backend
   python -m pytest tests/ -v -k "not test_extraction_accuracy"
   ```
   The unit tests, including the `test_gemma_ollama_adapter.py` mocks, will pass instantly.

3. **Run the Benchmark Test (Ollama Required)**:
   The accuracy harness requires a live Ollama instance. To prevent CI failures or local errors when Ollama is off, the test is protected by an environment variable. When you have Ollama running:
   ```bash
   # Linux/macOS
   RUN_BENCHMARK=1 python -m pytest tests/benchmark/test_extraction_accuracy.py -v -s
   
   # Windows PowerShell
   $env:RUN_BENCHMARK="1"; python -m pytest tests/benchmark/test_extraction_accuracy.py -v -s
   ```
   If Ollama is not reachable but `RUN_BENCHMARK=1` is set, the test will gracefully invoke `pytest.skip()` rather than crash.
