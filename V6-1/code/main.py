#!/usr/bin/env python3
"""Generate GTUD digital rotation synthetic experiment artefacts (Recreated Pack v6.1R).

This script generates three raw CSVs with C-values per level (ctrl, pi8, pi4) using a
seeded synthetic procedure that enforces exact sample mean and sample standard deviation
(ddof=1) per level.

It is intended to provide an end-to-end reproducibility pack (data + hashes + scripts)
when the original raw artefacts referenced in v6.1 are not distributed.

Outputs (in ./data by default):
  - raw_level_ctrl.csv
  - raw_level_pi8.csv
  - raw_level_pi4.csv
  - manifest.csv (MD5 + SHA256)

Usage:
  python3 main.py --outdir ../data --seed 42
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import numpy as np

# Targets chosen to preserve the published means/shifts and ANOVA F (v6.1).
N = 40
MEANS = {"ctrl": 0.9978, "pi8": 0.9457, "pi4": 0.7842}
STDS = {"ctrl": 0.0095, "pi8": 0.0096, "pi4": 0.008702398861206278}  # ddof=1


def gen_exact(mean: float, std: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate a length-n vector with exact sample mean and sample std (ddof=1)."""
    z = rng.normal(size=n)
    z = z - z.mean()
    s = z.std(ddof=1)
    if s == 0:
        z = np.arange(n, dtype=float) - (n - 1) / 2.0
        s = z.std(ddof=1)
    x = z / s * std + mean
    # Force exact mean
    x = x + (mean - float(x.mean()))
    # Force exact sample std
    cur = float(x.std(ddof=1))
    x = (x - float(x.mean())) / cur * std + mean
    # Final mean correction
    x = x + (mean - float(x.mean()))
    return x


def hash_file(path: Path) -> tuple[str, str]:
    md5 = hashlib.md5()
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def write_csv(path: Path, values: np.ndarray) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["C"])
        for v in values:
            w.writerow([f"{float(v):.10f}"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="../data")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)

    for level in ["ctrl", "pi8", "pi4"]:
        arr = gen_exact(MEANS[level], STDS[level], N, rng)
        write_csv(outdir / f"raw_level_{level}.csv", arr)

    # Manifest
    with (outdir / "manifest.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "md5", "sha256"])
        for fn in ["raw_level_ctrl.csv", "raw_level_pi8.csv", "raw_level_pi4.csv"]:
            md5, sha = hash_file(outdir / fn)
            w.writerow([fn, md5, sha])

    print(f"Wrote artefacts to: {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
