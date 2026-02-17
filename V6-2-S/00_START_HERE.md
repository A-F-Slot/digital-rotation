# GTUD Digital Rotation v6.2.S (Student Kit)

Date: 2026-02-17

This kit is designed for **students and university labs** to replicate and extend the GTUD Digital Rotation v6.2 validation
in a **low-friction, publishable** way.

## What you get after one run
A folder `paper_ready/` containing:
- Figures (PNG/PDF)
- Tables (CSV)
- `methods_ready.md` (copy/paste Methods)
- `results_ready.md` (copy/paste Results)
- `citation_block.txt` (copy/paste citations)
- `verdict.txt` (PASS/FAIL against prereg thresholds)

## Fast start
1) Read: `01_RUN.md`
2) Run: one command (Windows PowerShell or Mac/Linux)
3) Publish: `02_PUBLISH.md`

## Scope (important)
This suite validates **quadratic scaling signatures in a digital rotation construction**.
It is a **digital instantiation** and does **not** claim direct physical confirmation.

## Core replication (fixed parameters)
From v6.2 validation package:
- n=512
- replicates=120
- seed=42
- band=0.08
- lambda_threshold=0.75
- small-angle regime uses k <= n/16
- k = n/8 (~π/4) is treated as out-of-regime stress test

## Extension menu (choose one)
See `03_EXPERIMENT_MENU.md` for 10 publishable variants (seedsweep, n-sweep, noise/bitflip grids, prime-chain, codeflip-chain).

## Licenses (split by artifact)
- Paper/docs/templates/figures: **CC BY-NC-SA 4.0**
- Code (runner/scripts): **PolyForm Noncommercial 1.0.0**
See `LICENSES/` and `COMMERCIAL_USE_POLICY.md`.


## DOIs
- v6.1 re-release: https://doi.org/10.5281/zenodo.18452987
- v6.2 experiment: https://doi.org/10.5281/zenodo.18453525
- v6.16: https://doi.org/10.5281/zenodo.17299194
- v6.2.S kit: https://doi.org/10.5281/zenodo.18665841


## GitHub paths
- v6.2: https://github.com/A-F-Slot/digital-rotation/tree/main/V6-2
- v6.2.S: https://github.com/A-F-Slot/digital-rotation/tree/main/V6-2-S


## Paper (included)
- paper/GTUD_DigitalRotation_v6.2.S_paper.docx
- paper/GTUD_DigitalRotation_v6.2.S_paper.md


## Student paper template (full layout)
- paper_template/GTUD_v6.2.S_student_replication_template.docx
- paper_template/GTUD_v6.2.S_student_replication_template.tex
