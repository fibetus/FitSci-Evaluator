# FitSci - Design Specification (Bio-Signal UI)

This document captures the design essence of the existing **Hypertrophic-Research-Agent** frontend, to be preserved in the final **FitSci - Evaluator** application.

## 1. Aesthetic Identity: "The Bio-Signal Protocol"
The UI is designed to look like a high-security medical or research terminal. It evokes a sense of "Deep Tech" and "Scientific Rigor" through a futuristic, retro-terminal (CRT) aesthetic.

### Core Visual Elements
*   **Scanlines:** A repeating linear gradient overlay that mimics old CRT monitors.
*   **Grid Background:** A subtle 40px x 40px grid system to ground the data components.
*   **Phosphor Glow:** Strategic use of neon accents with soft outer glows (bloom effect).
*   **Typography:** 
    *   **JetBrains Mono:** For all technical data, labels, and "computer-generated" output.
    *   **Space Grotesk:** For high-level UI elements and readable findings.

## 2. Color Palette (Semantic Neon)
| Signal | Hex | Purpose |
| :--- | :--- | :--- |
| **Void** | `#0A0A0A` | Absolute background. |
| **Surface** | `#0F0F0F` | Component panels. |
| **Neon Green** | `#00FF41` | Success, high-confidence (90%+), and active signals. |
| **Neon Amber** | `#FFB700` | Moderate confidence, caveats, and warnings. |
| **Neon Red** | `#FF3131` | Low confidence, rejected studies, and critical risks. |
| **Neon Blue** | `#00D4FF` | Informational data, mechanisms, and IF scores. |
| **Neon Purple** | `#9D4EDD` | Practical application notes and tags. |

## 3. Component Architecture
*   **Bio-Header:** System status, versioning (v2.1), and a "LIVE" heartbeat indicator.
*   **Research Matrix (Heatmap):** A card-based grid showing study cards with vertical border indicators based on score color.
*   **Expert Analysis (Sidepanel):** A sticky sidebar providing a "Deep Dive" into findings, caveats, and practical notes.
*   **Confidence Gauge:** A radial SVG gauge with neon glow, visualizing the Methodology Confidence score.
*   **Delta Efficacy Chart:** A Recharts-powered bar chart comparing Test vs. Placebo group results.

## 4. Interaction Patterns
*   **Initialization Sequence:** A custom loader with "INITIALIZING BIO-SIGNAL PROTOCOL..." text and a database pulse.
*   **Staggered Entry:** Using `framer-motion` to animate components into view sequentially.
*   **Score-Based Dynamic Styling:** Colors and glow intensities update in real-time based on the selected study's credibility score.

---
*Derived from Hypertrophic-Research-Agent MVP.*
