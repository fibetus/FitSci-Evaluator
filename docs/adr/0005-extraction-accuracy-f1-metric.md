# 5. Extraction Accuracy F1 Metric

Date: 2026-05-10

## Status

Accepted

## Context

Phase 1 requires verifying that the Sifter (Gemma 4 Evaluator) extracts fields with an average accuracy of $\ge$ 80% F1 score across the 5 benchmark fixtures. Since the `Study` aggregate is a nested JSON structure with various data types (strings, lists, floats, nested dicts), computing a rigid "exact match" on every field would artificially deflate the accuracy score due to minor phrasing differences or list orderings (e.g. `["muscle mass", "hypertrophy"]` vs `["hypertrophy", "muscle mass"]`).

## Decision

We use a flattened structural F1 computation tailored for the 30+ field `Study` model:

1. **Flattening**: Expected (gold) and Actual (model) JSON dicts are flattened using dot notation (`delta.p_value`). Ignored fields (`score`, `confidence`, `quality_tier`, `score_breakdown`, `scraped_at`, `id`, `pmc_url`) are removed before comparison.
2. **Empty Handling**: If both Expected and Actual values are empty (null, `""`, `[]`), they are ignored entirely. They do not count as a True Positive (TP) to prevent inflating scores via sparse matrices.
3. **True Positives (TP)**:
   - For exact types (integers, floats, booleans), we require exact equality.
   - For text fields (strings), we use a substring/overlap check (if expected is a substring of actual or vice versa, ignoring case).
   - For lists, we check for a non-empty intersection of string representations, ignoring case.
4. **False Positives (FP)**: Model populated a field that was not in expected or did not match.
5. **False Negatives (FN)**: Expected was populated, but model was empty or did not match.
6. **Computation**: The standard harmonic mean of Precision and Recall is applied per document, and the final F1 is averaged across all benchmark fixtures.

## Consequences

- Minor spelling mistakes or rewordings by Gemma (e.g., "1.2 g/kg/d" vs "1.2g/kg/d") might still trigger a false negative if they don't substring match exactly, but the partial match significantly increases the realism of the score compared to strict equality.
- The minimum threshold of 80% is achievable and directly aligns with the "no hallucination" rule. If Gemma frequently hallucinates values where none exist, FP increases rapidly, tanking Precision and the F1 score.
