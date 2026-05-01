# FitSci Evaluator: Evidence-Based Fitness AI

> **A bridge between complex science and gym practice.** An intelligent system for analyzing and evaluating the credibility of scientific research related to training, nutrition, and hypertrophy.

---

## 1. The Problem

The fitness industry suffers from misinformation. Sensational headlines appear every day: *"New study: this supplement increases muscle mass by 50%!"* Unfortunately, most people training lack the competence or time to critically analyze scientific publications.

**Key problems:**
* **Interpretational errors:** Drawing conclusions from beginner-only studies that do not translate to trained athletes.
* **Ignoring statistics:** Missing the practical meaning of sample size, effect size, heterogeneity, and statistical significance.
* **Information noise:** Changing training plans every week because of isolated, low-quality reports.

## 2. The Solution

**FitSci Evaluator** uses structured extraction and scoring to act as a personal scientific reviewer. The system analyzes medical and sports publications, evaluates their methodology, and translates the result into practical training or nutrition guidance.

Instead of reading 20 pages of medical jargon, the user receives a **Credibility Verdict**, a bounded **Rigor Index**, and a practical note.

## 3. Hexagonal Architecture

FitSci Evaluator follows hexagonal architecture so the scientific rules stay independent from scraping, storage, CLI, API, and UI choices.

### Domain Core

* `backend/src/domain/models`: Pydantic models for studies, populations, deltas, dosage, score breakdowns, and quality tiers.
* `backend/src/domain/services`: pure domain services such as `ScoringService`. Domain services do not call external APIs, databases, or CLI code.
* `backend/src/domain/ports`: protocols that describe what the domain needs from the outside world, including ingestion, evaluation, and persistence.

### Adapters

* `backend/src/cli`: inbound CLI adapter that receives a study id, creates study data, and calls the domain scoring service.
* Planned outbound adapters: PubMed/PMC ingestion, LLM-backed study extraction, and repository persistence.

## 4. Scoring Contract

The scoring engine assigns points based on objective evidence-quality criteria:

* **Weight of evidence:** Meta-analyses receive the highest priority, then randomized trials, cohorts, narrative reviews, and case studies.
* **Population relevance:** Human studies and trained populations score higher than animal, in-vitro, sedentary, or untrained populations.
* **Sample size:** Larger samples increase confidence; very small samples receive penalties.
* **Recency and journal quality:** Recent publications and higher-impact journals receive modest positive weight.
* **Methodology and bias:** Placebo control, double blinding, preregistration, industry funding, and missing full text affect the breakdown.
* **Bounded Rigor Index:** The published score is always `0-14`, even when internal penalties appear in the breakdown.
* **Structured RCT handling:** Study type variants such as `rct_double_blind` count as methodology evidence even if duplicated boolean fields are missing.

Quality tiers:

* `high`: score `8-14`
* `moderate`: score `5-7`
* `rejected`: score `<5`

## 5. Local Usage

From the `backend` directory:

```bash
pip install -r requirements.txt
python -m pytest
python -m src.cli.main PMC12345
```

To use the `fitsci-evaluate` console script, install the package first (editable install recommended for development):

```bash
pip install -e .
fitsci-evaluate PMC12345
```

Or with Poetry:

```bash
poetry install
fitsci-evaluate PMC12345
```

## 6. Target Audience

* **Physique sports amateurs:** People who want to train smarter, not harder.
* **Personal trainers:** Coaches who need quick knowledge verification and client education.
* **Content creators:** Authors who want to build authority based on reliable evidence.

## 7. Implementation Plan

- [x] Establish the domain model for studies, populations, outcomes, dosage, and scoring metadata.
- [x] Define domain ports for ingestion, evaluation, and persistence.
- [x] Implement the pure domain scoring service with a bounded `0-14` Rigor Index.
- [x] Add a CLI adapter and package entry point for local evaluation.
- [ ] Implement a PubMed/PMC outbound ingestion adapter behind `IngestorPort`.
- [ ] Implement an LLM extraction adapter behind `EvaluatorPort`.
- [ ] Implement a repository adapter behind `RepositoryPort`.
- [ ] Add an application orchestration layer that coordinates ports without moving infrastructure concerns into the domain.
- [ ] Add API or UI inbound adapters after the domain flow is stable.

---

### Technologies

* **Language model:** Google Gemma family via Kaggle or Vertex AI
* **Backend:** Python, Pydantic, FastAPI
* **Architecture:** Hexagonal architecture with domain ports and adapters
* **Data processing:** Retrieval-augmented extraction and structured scoring

---

*Project created for the Kaggle hackathon: Gemma for Good.*
