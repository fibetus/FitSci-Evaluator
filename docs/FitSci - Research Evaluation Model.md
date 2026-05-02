# FitSci - Research Evaluation Models: Proposals & Justifications

Based on the analysis of *"Badania naukowe w treningu siłowym: interpretacja"*, this document presents three specialized models for evaluating scientific research within the FitSci ecosystem.

---

## Proposal 1: The Rigor Index (0–20 Points)
Focuses on the **methodological quality** and **statistical power** of the study.

### The Scoring Matrix
| Criterion | Metric | Points |
| :--- | :--- | :--- |
| **Evidence Level** | Meta-analysis / Position Stand | +6 |
| | RCT (Randomized Controlled Trial) | +4 |
| | Observational / Epidemiological | +1 |
| **Measurement Tool** | MRI (Gold Standard) | +4 |
| | Ultrasound (USG) | +2 |
| | DEXA (Lean Mass overestimation risk) | -1 |
| **Subject Status** | Resistance Trained (at least 6 months) | +3 |
| | Untrained / Beginners | +1 |
| **Statistical Depth** | Cohen's d (Effect Size) reported | +3 |
| | Narrow Confidence Intervals (95% CI) | +2 |
| | Only p-value reported (p < 0.05) | +0 |
| | p-value > 0.05 | -5 |

### Why these choices?
*   **MRI vs. DEXA:** The document highlights that DEXA cannot distinguish between actual muscle fibers and "cellular swelling" (water/glycogen), often overestimating results. MRI is the only tool for true cross-sectional area (CSA) measurement.
*   **Trained vs. Untrained:** Beginners respond to almost any stimulus (Newbie Gains), making it impossible to extrapolate results to advanced lifters.
*   **Cohen's d > p-value:** As the text states, p-value only tells you *if* a result isn't random; Cohen's d tells you *how strong* the effect actually is in the real world.

---

## Proposal 2: The Integrity Filter (Flag-based)
Focuses on identifying **biases** and **statistical manipulation** (p-hacking).

### Logic Flow
1.  **Funding Source:** If industry-funded (e.g., by a supplement company), mark with a ⚠️ **High Bias Alert**.
2.  **Conflict of Interest:** Check for "Researcher Degrees of Freedom".
3.  **Heterogeneity ($I^2$):** For Meta-analyses, if $I^2 > 50\%$, the study is "mixing apples with oranges." Flag as **Inconsistent Data**.
4.  **Surrogate Outcomes:** If the study measures acute spikes (e.g., MPS for 2 hours) rather than chronic adaptations (muscle growth over 8 weeks), flag as **Mechanistic Only**.

### Why these choices?
*   **P-hacking Awareness:** The document warns that researchers often torture data until it "confesses" a p < 0.05. The filter looks for signs of selective reporting.
*   **MPS vs. Growth:** The text emphasizes that acute Muscle Protein Synthesis (MPS) does *not* always correlate with long-term hypertrophy.

---

## Proposal 3: The APEASE Actionability Matrix
Translates scientific findings into **gym practice**.

### Evaluation Categories
*   **Practicality:** Can this be done in a standard gym?
*   **Effectiveness:** Is the Effect Size (Cohen's d) at least "Medium" (>0.5)?
*   **Acceptability:** Would an athlete actually stick to this protocol?
*   **Safety:** Does the method increase injury risk?

### Why these choices?
*   **Goldman's Dilemma:** Athletes are often willing to trade health for performance. This matrix prevents "reckless" implementation of experimental techniques.
*   **Small Effect Sizes:** If a study shows a "statistically significant" but "practically tiny" result (e.g., d = 0.15), the system advises: "Do not change your plan for this."

---

## Implementation in Gemma 4
The **FitSci Evaluator** will use these models to generate its "Credibility Verdict." 
*   **Step 1:** Gemma extracts the variables (N, tool, status, d, CI).
*   **Step 2:** The Scoring Engine calculates the **Rigor Index**.
*   **Step 3:** The Interpretation Layer cross-references with the **APEASE Matrix** to give the final tip.

---
*Referenced Document: Badania naukowe w treningu siłowym: interpretacja*
[[FitSci - Development Plan]] | [[FitSci - Evaluator context]]
