# FitSci Evaluator: Evidence-Based Fitness AI

> **A bridge between complex science and gym practice.** > An intelligent system for analyzing and evaluating the credibility of scientific research related to training, nutrition, and hypertrophy.

---

## 1. The Problem (Context)
The fitness industry suffers from a plague of misinformation. Sensational headlines appear every day: *"New study: this supplement increases muscle mass by 50%!"*. Unfortunately, most people training lack the competence to critically analyze scientific publications. 

**Key problems:**
* **Interpretational errors:** Drawing conclusions based on studies conducted on beginners (*noob gains*), which do not translate to advanced trainees.
* **Ignoring statistics:** Lack of understanding of statistical significance (*p-value*) and sample size (*N*).
* **Information noise:** Changing training plans every week under the influence of single, low-quality reports (so-called *Bro-Science*).

## 2. The Solution
**FitSci Evaluator** is an application utilizing advanced large language models (**Google Gemma 4**), acting as a personal scientific reviewer. The system automatically analyzes the content of medical and sports publications, evaluating their methodology and practical applicability.

Instead of reading 20 pages of medical jargon, the user receives a **Credibility Verdict** and a specific training tip.

## 3. How it Works (Architecture)

### A. Data Extraction (NLP)
The AI model analyzes the study text (PDF/Link) and extracts key parameters:
* **Study type:** (e.g., Meta-analysis, RCT, observational study, animal study).
* **Study group:** Sample size (*N*) and the training experience of the participants.
* **Statistical significance:** *p*-values and standard deviations.
* **Duration:** How long the intervention lasted.

### B. Scoring Algorithm (Scoring Engine)
The system assigns points based on objective *Evidence-Based Practice* criteria:
* **Weight of Evidence:** Meta-analyses receive the highest priority, case studies the lowest.
* **Beginner Filter:** A warning flag if the study involves untrained individuals.
* **P-Value Analysis:** Rejecting results with low statistical significance.

### C. Interpretation Layer
The LLM translates raw data into actionable insights:
* *"High-quality study – consider implementing this technique."*
* *"Small sample size study – treat this as a curiosity, do not change your plan."*

## 4. Target Audience
* **Physique Sports Amateurs:** Those who want to train smarter, not harder.
* **Personal Trainers:** Needing a tool for quick knowledge verification and client education.
* **Content Creators:** Wanting to build authority based on reliable data (Evidence-Based).

## 5. Development Potential (Roadmap)
- [ ] **PubMed API Integration:** Automatic retrieval of the latest studies.
- [ ] **Study Comparator:** Juxtaposing two conflicting publications and indicating which is methodologically stronger.
- [ ] **Supplement Database:** Automated supplement ranking based on aggregated scores from analyses.

---

### Technologies
* **Language Model:** Google Gemma 4 (via Kaggle/Vertex AI)
* **Framework:** Python, LangChain / LlamaIndex
* **Interface:** Streamlit / Gradio
* **Data Processing:** RAG (Retrieval-Augmented Generation)

---

### Development Resources
*   **Development Plan & Architecture:** [[FitSci - Development Plan]]

---
*Project created for the Kaggle hackathon: Gemma 4 Good.*
