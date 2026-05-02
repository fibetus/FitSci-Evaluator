# Audit — Gemma 4 Model Selection

**Date:** 2026-05-02
**Last reviewed by:** Claude Opus (automated audit)
**TL;DR:** Right-size to **Gemma 4 12B at Q4_K_M (≈7 GB)** for production extraction, with **Gemma 4 4B at Q4_K_M (≈2.7 GB)** as the dev/CI model. The Sifter task is structured information extraction over long inputs (3k–10k tokens of scientific text → 30+ JSON fields with strict types), which is too demanding for 1–4B models reliably but does not need 27B reasoning headroom. Run via Ollama locally for development and Vertex AI Model Garden for production, both behind the same `EvaluatorPort`.

> [CONFIDENCE: MEDIUM] — At the time of writing, "Gemma 4" appears in `/docs` as the project's named model family for the "Gemma 4 Good Hackathon" (`Development Plan` line 3). Public Gemma releases the auditor has high confidence in are Gemma 1, 2, and 3 (with Gemma 3 sizes 270M / 1B / 4B / 12B / 27B). The size-tier reasoning below assumes Gemma 4 follows a similar tiered family. If Gemma 4 ships with different size points, re-bucket using the same task-fit logic. **[MISSING INFO]** No `/docs` file specifies confirmed Gemma 4 size variants, context window, or licensing terms.

---

## 1. Recommended Variant

### Production: **Gemma 4 12B (instruct), quantized to Q4_K_M**
The task profile inferred from `/docs`:

| Workload signal | Source | Implication for size |
|---|---|---|
| Long-input structured extraction (full PMC paper → 30-field `Study` JSON) | `domain/models/study.py`; `Development Plan §M2` | Needs ≥8k context; 1B/4B can do JSON but degrade past ~3k tokens |
| Strict schema conformance (Pydantic-validated, `Literal` enums) | `study.py` lines 6–17 | Needs solid instruction-following; 4B is borderline for nested objects |
| Multilingual output (`summary_pl`, `summary_en`) | `study.py` lines 91–92 | Polish summarization is non-trivial below 12B in practice |
| Quantitative reasoning (parse N, p-value, Cohen's d, 95% CI from prose) | `Research Evaluation Model.md`; PDF source | Needs reliable numeric extraction; large gap between 4B and 12B here |
| Latency: a few-second per-paper interactive call | `Development Plan §4.2` (Swagger demo) | Must run on a single consumer GPU, not minutes per call |
| Cost: hackathon (`Development Plan` line 3) — no enterprise budget | Implicit | Rules out 27B as default — it requires ≥24 GB VRAM at Q4 |

**12B Q4_K_M** lands in the sweet spot:
- **VRAM at Q4_K_M:** ~7.0 GB → fits on a 12 GB consumer GPU (RTX 3060/4070), an Apple Silicon M-series Mac with ≥16 GB unified memory, or a single L4 on Vertex AI.
- **Schema-conformance reliability:** materially better than 4B for ≥10-field nested JSON; documented experience across the open-weights ecosystem.
- **Polish-language quality:** Gemma 3 12B is meaningfully better than 4B at non-English summarization; Gemma 4 is expected to retain or improve this gap. [CONFIDENCE: MEDIUM]

### Development / CI: **Gemma 4 4B (instruct), Q4_K_M**
- **VRAM:** ~2.7 GB. Runs on integrated GPUs / 8 GB cards / any modern laptop.
- **Use case:** the M2 benchmark suite (5 reference PMCIDs, asserted in `Development Plan §M2`) runs in CI. CI runners cannot host a 12B model, but a 4B model is enough to confirm prompt and adapter wiring correctness, with relaxed accuracy thresholds.
- The `EvaluatorPort` makes the swap to 12B a constructor argument.

### Reject: **1B**
Cannot reliably emit 30-field nested JSON from long context. Confirmed across the small-model ecosystem; not a Gemma-specific weakness.

### Reject: **27B (default)**
Needs ≥24 GB VRAM at Q4 (Vertex L4 minimum) for local; doubles inference cost vs 12B; the marginal accuracy gain on extraction-style tasks is small. Hold in reserve as the "upgrade tier" — see §4.

---

## 2. Quantization Recommendation

| Quantization | Size (12B) | Quality loss | Use? |
|---|---|---|---|
| FP16 (unquantized) | ~24 GB | None | ❌ Doesn't fit on single consumer GPU; overkill |
| Q8_0 | ~12.5 GB | <1% perplexity delta | ⚠️ Use if VRAM available and you want a known-clean reference run |
| **Q4_K_M** | **~7 GB** | **2–4% perplexity delta** | **✅ Default** |
| Q4_K_S | ~6.5 GB | 4–6% perplexity delta | ⚠️ Marginal saving; not worth the quality dip |
| Q3_K_M | ~5 GB | Noticeable JSON drift | ❌ Unsafe for structured output |
| Q2_K | ~4 GB | Severe | ❌ Will hallucinate fields and enum values |

### Format
- **GGUF via Ollama** locally (`ollama pull gemma4:12b-q4_k_m` syntax depending on the official tag).
- On Vertex AI, use the **bf16** weights served by Model Garden directly — Vertex hosts at full precision; quantization is a local-deployment optimization, not a cloud one.

### Constrained-output backstop
Quantization can occasionally tip JSON output across the validity edge (one missing brace, one wrong-cased enum). Defend the schema with:
- **Ollama `format: "json"`** parameter (forces grammar-constrained decoding).
- A library like **`outlines`** or **`instructor`** that does Pydantic-aware constrained decoding regardless of backend.
- Pydantic validation as the final gate — on `ValidationError`, retry with the validation message included in the prompt (max 1 retry, then surface a structured error).

---

## 3. Deployment Target

### Two-environment plan, single port
```
┌──────────────────────┐     ┌──────────────────────┐
│  GemmaOllamaAdapter  │     │  GemmaVertexAdapter  │
│  (dev, CI, demo)     │     │  (production)        │
└──────────┬───────────┘     └──────────┬───────────┘
           │                            │
           └─────── EvaluatorPort ──────┘
                       │
                  ScoringService (M3)
```

| Environment | Adapter | Backend | Why |
|---|---|---|---|
| **Local development** | `GemmaOllamaAdapter` | Ollama on developer laptop, model: `gemma4:12b-q4_k_m` (or `:4b-q4_k_m` on weak hardware) | No API keys, no quota, fast iteration on prompts. Stack analysis explicitly cites "5-line change" as the swappability target — Ollama makes that real. |
| **CI** | `GemmaOllamaAdapter` (4B) | Ollama in a GitHub Actions self-hosted runner, OR a recorded-response adapter (`GemmaReplayAdapter`) playing back fixed JSON for benchmark studies | CI must be deterministic and free; running 12B on hosted runners is impractical. |
| **Production** | `GemmaVertexAIAdapter` | Vertex AI Model Garden Gemma 4 12B endpoint, region `europe-west4` (data residency for Polish content) [CONFIDENCE: LOW — region depends on availability] | Auto-scaling, no GPU ops, audit logs. The hexagonal port absorbs the protocol difference (HTTP vs Ollama). |
| **Hackathon demo** | `GemmaOllamaAdapter` | Ollama on the demo machine | Air-gapped, no API key risk, no rate limits, no surprises. |

### Adapter sketch
```text
backend/src/adapters/ai/gemma_ollama.py
    class GemmaOllamaAdapter(EvaluatorPort):
        def __init__(self, model: str, base_url: str = "http://localhost:11434"): ...
        async def evaluate_text(self, text: str) -> Study:
            sanitized = sanitize(text)
            prompt = render_prompt(sanitized)
            raw = await self._client.generate(model=self.model, prompt=prompt, format="json", options={"temperature": 0.1})
            try:
                return Study.model_validate_json(raw)
            except ValidationError as e:
                return await self._retry_with_feedback(prompt, raw, e)
```

### What `Development Plan` Phase 1 must demonstrate
- One Ollama invocation against a real 12B (or 4B) model.
- One real PMC paper end-to-end through `GemmaOllamaAdapter`.
- Schema validation passing.
- Latency budget logged (target: <60s on 12B Q4 on consumer GPU).

---

## 4. Upgrade Threshold (when to move to 27B)

Define the threshold **quantitatively** so it isn't a vibe call:

| Trigger | Threshold | Action |
|---|---|---|
| **Field-level extraction accuracy on benchmark set** | <85% on 12B over 5 benchmark studies (per `Development Plan §M2 Validation`) after 3 prompt-engineering iterations | Try 27B; only if 27B clears 92%, upgrade. Otherwise the bottleneck is the prompt or the schema, not the model. |
| **Polish summarization fluency** | <4/5 average human rating across 10 summaries (assess via blind rating from one bilingual reviewer) | Upgrade for 27B *or* fine-tune 12B (cheaper long-term). |
| **Reasoning-heavy fields** (e.g. detecting p-hacking signals from prose, evaluating $I^2$ heterogeneity arguments) | Less than 70% agreement with Opus 4 evaluator | Upgrade *only if* the reasoning task remains in the LLM (vs being moved to deterministic logic in the Judge). Often the right move is to take the task out of the LLM. |
| **End-user latency requirement** | If 12B Q4 cannot stay under the chosen latency SLO (e.g. p95 < 60s on Vertex L4), and 27B at higher quantization isn't faster | Upgrade is the wrong move here; horizontal scale or batching is. |
| **Domain fine-tune is in scope** (`audit-finetuning-pipeline.md`) | Always | Fine-tune 12B first. A fine-tuned 12B beats a base 27B on narrow domains in published results across the LLM ecosystem. Skip 27B. |

**Rule of thumb:** if you find yourself wanting 27B, try fine-tuning 12B first (`audit-finetuning-pipeline.md`). The token-cost and VRAM math nearly always favors fine-tuning.

---

## 5. Rejected Alternatives

| Alternative | Why considered | Why rejected |
|---|---|---|
| **Gemma 4 1B** | Cheapest, runs anywhere | Cannot reliably emit nested JSON of this complexity over long inputs; verified pattern across small-model ecosystem |
| **Gemma 4 27B** as default | Best raw accuracy in the family | VRAM and cost-per-call too high; marginal accuracy gain over fine-tuned 12B on narrow extraction is small; held as the upgrade tier |
| **Gemini 1.5/2.0 Flash** | Cheap, hosted, huge context window | Project is explicitly a "Gemma 4 Good" hackathon submission; using Gemini violates the brief |
| **Closed-weights frontier (GPT-4o, Claude Sonnet, etc.)** for extraction | Highest reliability | Same brief violation; also breaks the open-source local-deployment story that the Bio-Signal/scientific-rigor narrative depends on |
| **Mixtral / Llama 3 70B** | Strong open weights | Brief violation; 70B is materially harder to self-host than Gemma 12B |
| **Phi-3 mini / Qwen 0.5–3B** | Tiny, fast | Same JSON-conformance failure mode as Gemma 1B; brief violation |
| **Gemma 4 12B at Q8_0** | Slight quality bump over Q4_K_M | Doubles VRAM (~12.5 GB), prices out 12 GB consumer GPUs; not worth a 1–3% perplexity gain |
| **Gemma 4 12B at FP16** | "Reference" quality | 24 GB VRAM, no consumer-GPU local dev, breaks the "5-line swap" promise of the Stack Analysis |

---

## 6. Operational Notes

- **Pin the model tag.** `gemma4:12b-q4_k_m` (or whatever the official Ollama tag becomes) — never use `latest`. Model digest pinning belongs in `.env.example` and in deployment manifests.
- **Cache responses by `(model_digest, prompt_hash)`.** Re-evaluating the same paper through the same model should be a cache hit, not a re-inference. Cache lives in the same PostgreSQL via a `llm_cache` table — *not* in the domain.
- **Log token counts and latencies** through a `MetricsPort` (recommended in architecture audit). The Phase 4 fine-tuning decision is data-driven; build the data infrastructure now.
- **Set `temperature=0.1` for extraction**, never higher. Higher temperatures improve generation diversity but actively harm structured extraction reliability.
- **Cap input length** at the model's context window minus a 1k buffer for prompt + output. For PMC papers exceeding the window, chunk by section (Abstract → Methods → Results → Discussion) and merge extractions, rather than truncating mid-document.

---

*End of Gemma 4 selection audit.*
