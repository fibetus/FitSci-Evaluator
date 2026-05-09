# FitSci - Evaluator: User Testing Walkthrough

Welcome to the **FitSci Evaluator**! This tutorial will guide you through setting up the application and evaluating real medical literature using our deterministic Judge and Gemma AI extraction. 

## Prerequisites
- **Python 3.11+**
- **Poetry** (Python package manager)
- **Ollama** installed on your system (for running the LLM locally)

---

## Step 1: Clone and Setup

First, navigate to the repository and install the backend dependencies using Poetry.

```bash
cd backend
poetry install
```

Copy the example environment variables to create your own configuration:
```bash
cp .env.example .env
```

Ensure your `.env` contains the required settings:
```ini
OLLAMA_BASE_URL=http://localhost:11434
GEMMA_MODEL_TAG=gemma4:12b-q4_k_m
```

---

## Step 2: Start the AI Engine (Ollama)

Before we run evaluations, we need to ensure the **Gemma 4** model is running locally. Start your Ollama service. If you haven't pulled the model yet, do so in a separate terminal:

```bash
ollama run gemma4:12b-q4_k_m
```
*(Note: If your system struggles with the 12B model, you can change `GEMMA_MODEL_TAG` in `.env` to a smaller model, e.g., `gemma4:4b`, but extraction quality might vary).*

Once you see the `>>>` prompt, Ollama is successfully running the model and exposing the API at `http://localhost:11434`.

---

## Step 3: Find a Real Study to Test

FitSci works by parsing raw scientific papers from the PubMed Central (PMC) database. You can pick any PMC ID, but here are some excellent real-world examples to try:

- **PMC4941165** - A classic Meta-Analysis by Brad Schoenfeld on training frequency. *(High Score)*
- **PMC4022420** - Jose Antonio's double-blind RCT on extreme high-protein diets. *(High Score)*
- **PMC2901358** - An animal model study on rats. *(Will be rejected by the Judge)*

---

## Step 4: Run the Evaluation Pipeline

We have implemented a CLI that runs the **Ingestor → Sifter → Judge** pipeline automatically.

Open your terminal in the root directory and use the CLI to evaluate the study. Let's use the high-protein RCT (`PMC4022420`) as an example:

```bash
cd backend
python -m src.cli.main evaluate PMC4022420
```

### What happens in the background?
1. **The Ingestor** (`PMCAdapter`) fetches the full XML text of the study directly from the NCBI E-utilities. The raw bytes are cached locally so subsequent runs are instant.
2. **The Sifter** (`GemmaOllamaAdapter`) passes the raw text wrapped securely in `<paper>` tags to your local Gemma model. It strictly asks for a structured JSON matching our `Study` model. If Gemma makes a validation error, the Sifter automatically retries using a prompt-feedback loop!
3. **The Judge** (`ScoringService`) receives the structured data. It applies our deterministic *Rigor Index* to calculate the final `score`, `confidence`, and `quality_tier` entirely in Python—Gemma does not dictate the score!

---

## Step 5: Review the Output

When the pipeline finishes, the CLI will output the final `Study` JSON. Pay close attention to:

- **`quality_tier`**: Did it get a "high", "moderate", or "rejected" rating?
- **`score`**: Look at the `score_breakdown`. You'll see exactly *why* the study got its score (e.g., +4 for double-blind RCT, +2 for human population).
- **`summary_en` / `key_findings`**: Notice how Gemma extracted the actual scientific outcomes.
- **`delta`**: The exact numbers (e.g., percentage change in muscle mass) extracted directly from the results section.

### Test the Deterministic Rejection
Try running an animal study:
```bash
python -m src.cli.main evaluate PMC2901358
```
You will notice the `quality_tier` is strictly set to `"rejected"` because `is_human_study` is `false`. The final published `score` is clamped to `0`, while the `score_breakdown` will still show the negative penalties that drove the raw total below zero.

---

## Troubleshooting

- **Timeout Errors**: Large meta-analyses can take 1-3 minutes for the 12B model to process on consumer hardware. Wait patiently, or ensure your Ollama is utilizing your GPU.
- **ExtractionError**: If the LLM repeatedly fails to output valid JSON despite the retry mechanism, you might be using a model smaller than 12B, which struggles with complex 30-field nested JSON constraints.
- **IngestionError**: Check your internet connection; the system needs to reach `ncbi.nlm.nih.gov`.

**Enjoy exploring the literature with FitSci!**
