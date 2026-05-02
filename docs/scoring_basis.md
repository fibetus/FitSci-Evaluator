# FitSci Scoring Basis

This document captures the current scoring basis used by `ScoringService.calculate_rigor_index`.

Source of truth used to compile this file:
- `backend/src/domain/services/scoring.py`
- `backend/tests/test_scoring.py`

> Note: `GEMINI.md` is referenced in code comments, but was not found in this repository snapshot.

## Rigor Index Components

### 1) Study Type
- `meta-analysis`: +5
- double-blind + placebo-controlled: +4
- single double-blind OR `rct_crossover`: +3
- `cohort_prospective` with `sample_size > 100`: +2
- `review_narrative`: +1

### 2) Population
- Human + trained: +2
- Human + not trained/other: +1
- Non-human (animal / in-vitro): -5

### 3) Sample Size
- `sample_size >= 200`: +2
- `50 <= sample_size < 200`: +1
- `0 < sample_size < 10`: -3

### 4) Recency
- `year >= 2024`: +2
- `year >= 2022`: +1
- `year < 2019`: -1

### 5) Impact Factor
- `impact_factor >= 10`: +2
- `impact_factor >= 5`: +1
- `impact_factor < 2`: -1

### 6) Methodology
- placebo-controlled: +1
- double-blind: +1
- preregistered: +1

### 7) Bias
- industry-funded flag: -1
- no full text flag: -1

## Aggregate Score and Tier

`score` is the sum of all points from sections above.

Quality tier thresholds:
- `score >= 8` -> `high`
- `5 <= score <= 7` -> `moderate`
- `score < 5` -> `rejected`

## Confidence Calculation

1. `base_score = (max(0, raw_pts) / 14) * 100`
2. multiplier:
   - `meta-analysis`: `1.0`
   - double-blind + placebo: `0.85`
   - any `rct*`: `0.75`
   - otherwise: `0.5`
3. bonuses:
   - `i_squared < 25`: `+10`
   - `i_squared > 75`: `-15`
   - `citation_count > 50`: `+8`
   - `citation_count > 10`: `+4`
4. `confidence = int(clamp(base_score * multiplier + bonuses, 0, 100))`
