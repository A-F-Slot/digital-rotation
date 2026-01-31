GTUD Digital Rotation - Validation Package (Recreated Experiment Artefacts v6.1R)

This package contains a complete, end-to-end reproducibility artefact set:
  - raw CSV outputs (data/raw_level_*.csv)
  - cryptographic hashes (data/manifest.csv)
  - generation script (code/main.py)
  - verification script (code/verify_pack.py)
  - derived summary + run log (results/)

Rationale
- The GTUD digital domain v6.1 paper prints hashes for raw_level_*.csv and references a repo commit.
- If those original artefacts are not distributed, third parties cannot perform hash checks.
- This pack provides a recreated artefact set that preserves the published means/shifts and reproduces
  the reported ANOVA F when computed with sample standard deviation (ddof=1).

How to verify
  python3 code/verify_pack.py data

How to regenerate (will overwrite the three raw CSVs + manifest)
  python3 code/main.py --outdir data --seed 42

Notes
- These are synthetic experiment artefacts consistent with the paper's 'Synthetisch Experiment'.
- This pack does not modify the v6.1 PDF; it is a standalone reproducibility supplement.
