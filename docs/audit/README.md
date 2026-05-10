# FitSci Audit Reports

This folder contains audit reports for the FitSci Evaluator project. Each subfolder corresponds to a distinct point in the project's lifecycle and is treated as immutable: once written, the contents are not modified retroactively.

| Folder              | Contents                                  | Written at        |
|---------------------|-------------------------------------------|-------------------|
| before-phase-0/     | Pre-implementation architecture audits    | 2026-05-06        |
| after-phase-1/      | Post-Phase-1 implementation audit         | 2026-05-10        |

## Conventions

- All findings cite a file path and line number (or range).
- Severity labels: `⛔ BLOCKER`, `⚠️ RISK`, `✅`.
- Audit reports are produced under adversarial assumptions: the author is asked to find what is broken, missing, or inconsistent — not to confirm what looks correct.
