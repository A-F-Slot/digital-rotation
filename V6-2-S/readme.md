# GTUD Digital Rotation v6.2.S (Student Kit)

One-day replication + falsification suite for the GTUD Digital Rotation v6.2 digital experiment.
Single-command run → `paper_ready/` bundle (figures, CSV tables, manifest, hashes) + PASS/FAIL verdict.

## Quick start
- Windows: run `run.ps1`
- macOS/Linux: run `run.sh`

Outputs are written to: `paper_ready/`

## What we test (binary sets / conditions)
- Baseline (reference-matching): `coherent_bin_clean`
- Negative controls (must FAIL): `random_bin`, `palindrome_bin_no_coherence`
- Optional extensions (if enabled in your run): `llm_bin`, `prime_bin`, `code_bin`

## Official replication rule (no ambiguity)
You may claim an **OFFICIAL replication** of v6.2/v6.2.S only if you attach these four files:

1) `paper_ready/verdict_details.json`
2) `paper_ready/run_manifest.json`
3) `paper_ready/hashes.txt`
4) `paper_ready/tables/fit_summary_by_condition.csv`

If you do not provide all four, your work is a **VARIANT / reimplementation (not comparable)**.

## Verdict logic (high-level)
OFFICIAL PASS requires:
- Baseline metrics match the bundled v6.2 reference within tolerances (reference-matching), AND
- Negative controls fail (do not accidentally look quadratic), preventing false positives.

See `paper_ready/verdict_details.json` for the exact thresholds and measured values.

## One-command validation (recommended)
Run:
- `python tools/check_official_replication.py paper_ready`

This prints:
- `OFFICIAL_REPLICATION_PASS`, `OFFICIAL_REPLICATION_FAIL`, or `NOT_COMPARABLE`

## Citation (official vs variant)
OFFICIAL replication (PASS or FAIL):
- Cite the Student Kit DOI: https://doi.org/10.5281/zenodo.18665841
- Cite the v6.2 experiment DOI: https://doi.org/10.5281/zenodo.18453525

VARIANT / not comparable:
- Cite as related work only, and label your work explicitly as “not comparable to the official v6.2.S pipeline”.

## License note (noncommercial)
Docs/templates: CC BY-NC-SA 4.0
Code: PolyForm Noncommercial 1.0.0
