# Audit — Fine-Tuning Pipeline Design

**Date:** 2026-05-02
**Last reviewed by:** Claude Opus (automated audit)
**TL;DR:** Recommended pipeline: scrape expert opinions + extract Q/A pairs from reviewed PMC papers → score every example with Claude Opus 4 (or equivalent) using a domain-specific rubric → keep ~5–10k high-quality instruction triples → **QLoRA-fine-tune Gemma 4 12B**, never the base 27B and never a full fine-tune. Deploy the LoRA adapter behind the same `EvaluatorPort` as the base model, A/B-test via a `RoutingEvaluatorAdapter`, roll back by swapping a config flag. Estimated cost: a few hundred USD on a single H100/A100 hour-block, vs thousands for full fine-tuning.

> [CONFIDENCE: MEDIUM] — The user's prompt mentions "Hermes" as the scraper. The audit interprets this as a generic web-scraping tool / framework (not Nous Research's Hermes LLM). If "Hermes" refers to a specific in-house tool, the data acquisition strategy applies the same way; only the scraping mechanics differ.
> [MISSING INFO] — `/docs` does not currently mention fine-tuning at any phase. This document is therefore proposing a new Phase 4 (or post-hackathon track) rather than auditing an existing plan.

---

## 1. Data Acquisition

### 1.1 Sources (in priority order)

| # | Source | Why | Realistic volume | Format |
|---|---|---|---|---|
| 1 | **PMC Open Access Subset** (already accessible via `IngestorPort.PMCAdapter` from M1) | Free, structured, full-text XML, license permits derivative works (open-access papers only) | ~500–5,000 papers per scoped query (e.g. *resistance training hypertrophy* 2018+) | NXML/JATS XML |
| 2 | **Position Stands** from ISSN, IOC, ACSM, NSCA, EFSMA | Highest-tier evidence, written in expert voice — closest match to FitSci's target output style | ~50–200 documents | PDF (mostly), HTML some |
| 3 | **Curated expert blogs** with explicit reuse permission (e.g. StrongerByScience, Damian Parol's blog cited in source PDF) | Reasoning-style writing — exactly the voice the fine-tuned model should adopt | ~100–500 articles | HTML |
| 4 | **PubMed abstracts + structured metadata** | Cheap to harvest, useful for the Sifter extraction sub-task | 10,000+ | XML (eutils) |
| 5 | **YouTube transcripts of credentialed experts** (Brad Schoenfeld, Mike Israetel, etc.) — **only with explicit written permission** | Spoken style is closer to lay-person Q/A than papers | Variable | Whisper-transcribed |

❌ **Do NOT scrape**: any source whose ToS forbids scraping; any source without reuse rights; any anonymous Reddit/forum content (reproduces the misinformation the project was built to fight).

### 1.2 Hermes scraping strategy

For each source the scraper must:
- Respect `robots.txt` and `crawl-delay`. Document compliance.
- Persist a license-or-permission record for every fetched document. **No record → no inclusion in the dataset, no exceptions.**
- Cache HTML/PDF/XML bytes immutably so re-extraction (e.g. better parsing later) doesn't require re-scraping.
- Emit a normalized `RawDocument` schema:
  ```python
  class RawDocument(BaseModel):
      source_id: str          # PMCID, URL, DOI
      source_type: Literal["pmc","blog","position_stand","abstract","transcript"]
      url: str
      license: str            # "cc-by-4.0", "cc-by-nc-4.0", "permission_emailed", etc.
      retrieved_at: datetime
      raw_bytes_path: str     # path/URI to immutable archive
      text: str               # cleaned plain text
      metadata: dict          # source-specific
  ```
- Live in `adapters/scraping/hermes_adapter.py` behind a `domain/ports/scraping/raw_document_source.py` port. **The fine-tuning pipeline must not depend directly on Hermes** — same hexagonal rule.

### 1.3 Volume target — what is realistic?

For meaningful domain adaptation of Gemma 4 12B via QLoRA on **structured extraction + lay-style summarization**:

| Dataset size | Effect |
|---|---|
| <1,000 examples | Insufficient — high variance, prone to overfitting |
| **5,000–10,000 examples** | **Sweet spot for QLoRA** on a narrow domain; converges in ~3 epochs |
| 50,000+ | Diminishing returns relative to data-curation cost |

Translating to scraping volume: budget **~3× the target** (e.g. 20,000 raw scraped items) because the evaluator (§2) will reject ~60–80%.

### 1.4 Conversion to instruction triples

The fine-tune dataset format is `{instruction, input, output}` (Alpaca-style) or messages-style. For FitSci, two task types exist:

**Task A — Extraction (mirrors M2):**
```json
{"instruction": "Extract the FitSci Study schema from the paper text below.",
 "input": "<paper-text>...full PMC body...</paper-text>",
 "output": "<full Study JSON>"}
```
Generated automatically: take a paper that has *already* been evaluated by the production Sifter on Gemma 4 12B + manually corrected. The corrected JSON is the gold output.

**Task B — Lay-style summarization (mirrors Translator feature):**
```json
{"instruction": "Translate the following Study JSON into a 3-sentence Polish gym-floor summary in NTS style.",
 "input": "<full Study JSON>",
 "output": "Krótkie streszczenie po polsku..."}
```
Generated semi-automatically: take expert blog summaries (from sources #3 above) where the underlying paper is identifiable, pair them.

### 1.5 Quality filtering before evaluation

Cheap deterministic gates run *before* the expensive LLM evaluator:
- **License gate.** Drop anything without a verified reuse license.
- **Length gate.** Drop docs <500 chars (stub pages) or >100k chars (book-length, not chunkable cleanly).
- **Language gate.** Detect language; keep only Polish + English.
- **Topic gate.** Embed-and-classify against the `StudyTopic` enum (`hypertrophy`, `protein`, `creatine`, ...); drop off-topic.
- **Deduplication.** MinHash or simple URL+title hash; near-duplicates inflate the dataset and break the train/eval split.

Every dropped item must be logged with the reason — a fine-tune dataset whose curation isn't auditable is itself "garbage in."

---

## 2. Evaluation Layer (Opus 4 / Claude-level model)

### 2.1 Why a frontier evaluator
A small/local model cannot reliably distinguish "well-reasoned, methodologically sound expert text" from "confidently wrong gym-bro content." The evaluator's job is to be a **stand-in domain expert at scale**. The premium-tier model is used for ~30k evaluator calls (one per candidate example), then never again — the cost is bounded.

### 2.2 Evaluator prompt design

The evaluator runs in **batch mode**, scoring one example at a time:

```text
You are a sport-science methodology reviewer. Score the candidate training example
below against the rubric. Be strict; the goal is to filter for fine-tuning quality,
not to be encouraging.

CANDIDATE TASK TYPE: {extraction|summarization}
CANDIDATE INPUT:
<input>{input_text}</input>

CANDIDATE OUTPUT:
<output>{output_text}</output>

RUBRIC:
1. Factual accuracy vs the input (1-5)
2. Methodological literacy — correctly distinguishes Cohen's d from p-value,
   correctly weights MRI > USG > DEXA, flags untrained-vs-trained extrapolation (1-5)
3. Schema conformance (extraction tasks only): valid JSON, all required fields,
   correct enum values (1-5; 0 if invalid)
4. Voice fit — sober, evidence-based, no hype (1-5)
5. Hallucination check — does the output assert anything not supported by the input? (1-5; 5 = no hallucinations)

Respond with strict JSON:
{
  "factual": int, "methodology": int, "schema": int, "voice": int, "hallucination": int,
  "rationale": "one sentence per dimension explaining the score",
  "verdict": "accept" | "reject" | "manual_review",
  "confidence": float  // 0.0–1.0
}
```

### 2.3 Scoring rubric & threshold

| Dimension | Weight | Reject threshold |
|---|---|---|
| Factual accuracy | 25% | any score ≤2 → auto-reject |
| Methodology | 25% | any score ≤2 → auto-reject |
| Schema conformance (extraction) | 20% | score 0 → auto-reject |
| Voice fit | 10% | — |
| Hallucination | 20% | any score ≤3 → auto-reject (this is a fitness-misinformation project; hallucination is the cardinal sin) |

Composite ≥ 4.0/5 weighted **and** evaluator `confidence ≥ 0.75` and `verdict == "accept"` → keep.
Composite 3.0–4.0 or `confidence < 0.75` → `manual_review` queue.
Anything else → reject.

### 2.4 Handling evaluator disagreement / low confidence

- Run the evaluator **twice** on a stratified 5% sample; if disagreement on `verdict` exceeds 10%, the rubric is too vague — refine before continuing.
- All `manual_review` items go to a human-in-the-loop queue; cap at ~500 items (anything bigger means the rubric needs tightening, not more humans).
- Track evaluator drift: rerun a fixed 100-item canary set monthly. If scores shift, freeze the evaluator model version (`claude-opus-4-2026-05-...` or whichever pinned snapshot).

### 2.5 Cost control
- Cache by `(input_hash, output_hash, evaluator_model_digest)`.
- Use the cheapest tier of the frontier model that maintains rubric agreement with humans on a 100-item ground-truth set. Test Sonnet first, escalate to Opus only if agreement is <85%.
- Strict batch size; never call the evaluator interactively.

---

## 3. Fine-Tuning Execution

### 3.1 Method choice — QLoRA, justified

| Method | Why considered | Decision |
|---|---|---|
| **Full fine-tune (FFT) of 12B** | Best raw quality | ❌ Requires 80+ GB VRAM × multiple GPUs; thousands of USD; overwrites general knowledge → *catastrophic forgetting* on out-of-domain queries |
| **LoRA on 12B** | Cheap, preserves base weights | ⚠️ Good but still needs ~24 GB VRAM; QLoRA is strictly better at this scale |
| **QLoRA on 12B** | NF4 base + LoRA adapters; fits 12B fine-tune on a single 24 GB GPU; published as the standard for narrow-domain adaptation | ✅ **Chosen.** A single H100 / A100 80 GB → comfortable; a single 4090 24 GB → tight but feasible. |
| **Prompt-tuning (soft prompts only)** | Minimal compute, ~few-hundred examples enough | ⚠️ Use as the **first experiment** to validate the data pipeline cheaply. If prompt-tuning lifts evaluator scores by ≥10%, skip QLoRA. |
| **DPO / preference tuning** | Aligns to expert preferences | ⚠️ Phase-2 fine-tune, after a working SFT model exists; requires preference pairs, not just gold outputs |
| **QLoRA on 27B** | Higher ceiling | ❌ Doubles compute; documented domain-fine-tuned 12B beats base 27B on narrow tasks; not worth it |

**Recommended sequence:**
1. **Prompt-tune** with 200–500 hand-picked examples — 1 day, ~$10. Measures whether the data is even discriminative.
2. **QLoRA SFT** on the full curated 5–10k dataset — 1–2 days, ~$200–400 on rented H100.
3. Optional later: **DPO** with preference pairs harvested from the evaluator's `manual_review` queue.

### 3.2 Hyperparameters (starting points)

| Param | Value | Notes |
|---|---|---|
| Base model | `gemma-4-12b-it` (instruct variant) | Use the instruct variant; chat formatting is preserved |
| Quantization | NF4 (4-bit) for the base, bf16 for the adapters | Standard QLoRA |
| LoRA rank `r` | 16–32 | 16 for narrow style adaptation; 32 if including extraction |
| LoRA alpha | `2 × r` | Conventional |
| Target modules | `q_proj, k_proj, v_proj, o_proj` (and optionally `gate_proj, up_proj, down_proj`) | Attention-only first; widen if loss plateaus |
| Learning rate | `2e-4` | QLoRA-typical |
| Batch size (effective) | 16–32 (use grad accumulation) | |
| Epochs | 2–3 | More than 3 → overfit on 10k examples |
| Sequence length | 8192 | Match expected paper-section chunk size |
| Eval cadence | every 200 steps on a held-out 10% split | |

### 3.3 Dataset size — meaningful adaptation threshold

| Sub-task | Minimum useful | Recommended |
|---|---|---|
| Style/voice adaptation (NTS-style summaries, Polish gym-floor tone) | ~1,000 examples | 3,000–5,000 |
| Extraction conformance (forcing the 30-field `Study` schema with high reliability) | ~3,000 well-labeled examples | 5,000–8,000 |
| Both combined | 5,000 | 8,000–10,000 |

Below 1,000 examples, prompt-tuning dominates QLoRA. Above 20,000, returns flatten — invest in *quality* (rubric tightening, manual review) instead of more scraping.

### 3.4 Evaluation metrics post fine-tune

**BLEU/ROUGE are not sufficient** for this domain. Use:

| Metric | What it measures | How |
|---|---|---|
| **Extraction field-level F1** | Per-field precision/recall against gold `Study` JSONs on a held-out 100-paper set | Compute on each `Literal` enum field, each numeric field (with tolerance), each list field |
| **Schema validity rate** | % of outputs that pass `Study.model_validate` | Trivial; must be ≥99% post-fine-tune |
| **Hallucination rate** | % of outputs asserting facts not in the input | Sample 200 outputs, ask Opus 4 evaluator to flag unsupported claims; target <2% |
| **Voice match score** | Blind human rating on 1–5 vs gold expert summaries | Bilingual reviewer, double-blinded, n≥50 |
| **Rubric uplift vs base** | Same evaluator rubric (§2) applied to base-Gemma-12B vs fine-tuned-Gemma-12B on 200 fresh prompts | Must show ≥0.5/5 composite improvement on the methodology + voice dimensions to justify the deploy |
| **Out-of-domain regression** | Performance on a generic benchmark (e.g. MMLU subset, IFEval) | Must not drop more than 5% — guards against catastrophic forgetting |
| **Latency parity** | p95 inference time vs base | LoRA adapters add negligible overhead; if you see >5% slowdown, the merge is wrong |

### 3.5 Overfitting safeguards
- **Strict 80/10/10 split** of the curated dataset; train on 80%, eval during training on 10%, hold-out 10% touched only at the very end.
- **Source diversity check:** no single source (e.g. one author's blog) exceeds 15% of the training set.
- **Topic balance:** stratify across the `StudyTopic` enum; oversample under-represented topics (e.g. `peptides`, `injury`).
- **Early stopping** on held-out loss plateau ≥ 200 steps.
- **Out-of-domain regression test** (above) is a release gate, not a "nice to have."
- **Adversarial probe set** of 50 known fitness myths from the source PDF. The fine-tuned model must not endorse any of them. If it does, reject the fine-tune.

---

## 4. Hexagonal Integration

### 4.1 Where the fine-tuned model lives
- The fine-tuned LoRA adapter is **just another `EvaluatorPort` adapter** — there is no domain change.
- New file: `backend/src/adapters/ai/gemma_finetuned_ollama.py` (loads `gemma-4-12b-finetuned-fitsci-v1` model tag in Ollama, or hosts the merged weights via vLLM in production).
- The base `GemmaOllamaAdapter` and the fine-tuned adapter implement the **identical** `EvaluatorPort` interface.

### 4.2 A/B testing behind one port

Introduce a `RoutingEvaluatorAdapter` that itself implements `EvaluatorPort` and *delegates* to one of N child adapters based on a configured routing policy:

```text
backend/src/adapters/ai/routing_evaluator.py

class RoutingEvaluatorAdapter(EvaluatorPort):
    def __init__(self, base: EvaluatorPort, finetuned: EvaluatorPort, 
                 router: RoutingPolicy, telemetry: MetricsPort): ...
    async def evaluate_text(self, text: str) -> Study:
        chosen = self.router.choose()       # e.g. 90% base / 10% finetuned, or hash(study_id)%10
        t0 = time.monotonic()
        result = await chosen.evaluate_text(text)
        self.telemetry.record(model=chosen.name, ms=elapsed, schema_ok=...)
        return result
```

Routing policies:
- **Canary:** 95% base / 5% fine-tuned for the first week.
- **Hash-bucketed:** stable per-study assignment (idempotent re-evaluation always uses the same model).
- **Always-fine-tuned + shadow-base:** call both, return fine-tuned, compare offline.
- **Manual override:** a `?model=` query parameter on `POST /evaluate` for A/B testing from the UI.

The use case (`EvaluateStudyUseCase`) doesn't know any of this exists — it sees one `EvaluatorPort`.

### 4.3 Rollback strategy

Three independent rollback levers, smallest blast radius first:

| Lever | Time to rollback | Trigger |
|---|---|---|
| **Routing weight → 100% base** | seconds (config flip) | Telemetry shows fine-tuned model schema-validity drop, latency spike, or cost spike |
| **Disable fine-tuned adapter from DI registration** | minutes (deploy) | Fine-tuned adapter is producing hallucinated content but routing config is misbehaving |
| **Republish previous fine-tune version `v(N-1)`** | minutes (model tag swap in Ollama / Vertex) | New fine-tune is worse than the previous one |

Every fine-tune ships a **versioned LoRA adapter file** with an immutable tag (`fitsci-finetune-v3-2026-06-01`). Never overwrite a previous version. Keep at least the last 3.

### 4.4 Evaluation-as-port

The post-fine-tune metrics (§3.4) should be runnable by a **`FineTuneEvaluator` use case** that:
1. Loads a benchmark set from `RepositoryPort` (or a fixtures file),
2. Runs both the base and the fine-tuned `EvaluatorPort` adapters via `RoutingEvaluatorAdapter` in shadow mode,
3. Computes F1 / hallucination / schema validity,
4. Persists results to a `model_evaluations` table.

This makes "is the new fine-tune deployable?" a one-command answer, repeatable, scriptable in CI.

### 4.5 What stays in the domain
- The `EvaluatorPort` contract — never grows new methods just to accommodate fine-tuned-specific features.
- The `Study` schema — fine-tuning must not require schema changes.
- The Judge (M3) — never fine-tuned. The score is *deterministic*, by project ethos.

### 4.6 What never goes in the domain
- LoRA adapter files, tokenizer configs, `bitsandbytes` calls, `peft` imports.
- Prompt templates (those live in `adapters/ai/prompts/`).
- Anything from the `transformers` / `peft` / `trl` libraries.

---

## 5. Risks specific to fine-tuning

| Risk | Mitigation |
|---|---|
| Evaluator (Opus 4) is itself biased on Polish-language sport-science | Cross-validate evaluator on a 100-item human-graded ground-truth set in Polish before bulk evaluation; report inter-rater agreement |
| Catastrophic forgetting: fine-tuned model loses general reasoning, gives wrong answers on edge-case fields | Out-of-domain regression test (§3.4) as release gate |
| Dataset poisoning: a popular-but-wrong blog gets included and teaches the model bro-science | Source allow-list, methodology score gate (§2.3), adversarial probe set (§3.5) |
| Fine-tune leaks copyrighted text verbatim | License gate at scrape time, deduplication, eval prompts asking the model to recite long passages — should refuse |
| Fine-tune is great offline, worse on real users | Canary routing (§4.2) plus telemetry-driven rollback (§4.3); never go from 0% → 100% in one step |
| Prompt-injection resistance regresses post-fine-tune | Include adversarial-prompt examples in the *training set* with the correct refusing/structured response; test post-train |
| Unbounded compute spend | Budget envelope per fine-tune run (e.g. $500 cap); stop training on plateau; never auto-rerun on commit |

---

*End of fine-tuning pipeline audit.*
