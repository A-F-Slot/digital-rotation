#!/usr/bin/env python3
"""Verify hashes and recompute stats for the Recreated Pack v6.1R.

Usage:
  python3 verify_pack.py ../data

Checks:
  - MD5 + SHA256 match manifest.csv
  - Recomputes mean/std (ddof=1), shifts, ratio, and ANOVA.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from scipy.stats import f_oneway
except ImportError:
    f_oneway = None


def hash_file(path: Path) -> tuple[str, str]:
    md5 = hashlib.md5()
    sha = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def load_vec(path: Path) -> np.ndarray:
    if pd is not None:
        df = pd.read_csv(path)
        for col in ['C','value','values','corr','correlation']:
            if col in df.columns:
                return df[col].to_numpy(dtype=float)
        # fallback first numeric
        for col in df.columns:
            if np.issubdtype(df[col].dtype, np.number):
                return df[col].to_numpy(dtype=float)
    # fallback numpy
    return np.loadtxt(path, delimiter=',', skiprows=1, dtype=float)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('data_folder', nargs='?', default='../data')
    args = ap.parse_args()

    folder = Path(args.data_folder).resolve()
    manifest = folder / 'manifest.csv'
    if not manifest.exists():
        print('Missing manifest.csv')
        return 2

    expected = {}
    with manifest.open('r', newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            expected[row['file']] = (row['md5'].lower(), row['sha256'].lower())

    ok = True
    for fn, (md5_exp, sha_exp) in expected.items():
        p = folder / fn
        if not p.exists():
            print(f'Missing: {fn}')
            return 2
        md5_got, sha_got = hash_file(p)
        md5_ok = (md5_got == md5_exp)
        sha_ok = (sha_got == sha_exp)
        print(f"{fn}: MD5 {'OK' if md5_ok else 'FAIL'}; SHA256 {'OK' if sha_ok else 'FAIL'}")
        if not (md5_ok and sha_ok):
            ok = False
    if not ok:
        return 3

    ctrl = load_vec(folder/'raw_level_ctrl.csv')
    pi8  = load_vec(folder/'raw_level_pi8.csv')
    pi4  = load_vec(folder/'raw_level_pi4.csv')

    def summ(v):
        return float(np.mean(v)), float(np.std(v, ddof=1))

    m_ctrl, s_ctrl = summ(ctrl)
    m_pi8, s_pi8 = summ(pi8)
    m_pi4, s_pi4 = summ(pi4)

    shift_pi8 = 100.0*(m_pi8 - m_ctrl)/m_ctrl
    shift_pi4 = 100.0*(m_pi4 - m_ctrl)/m_ctrl
    ratio = shift_pi4/shift_pi8

    print('
level,n,mean_C,std_C,shift_pct')
    print(f"ctrl,{len(ctrl)},{m_ctrl:.6f},{s_ctrl:.6f},0.000000")
    print(f"pi8,{len(pi8)},{m_pi8:.6f},{s_pi8:.6f},{shift_pi8:.6f}")
    print(f"pi4,{len(pi4)},{m_pi4:.6f},{s_pi4:.6f},{shift_pi4:.6f}")
    print(f"
ratio (pi4/pi8) = {ratio}")

    if f_oneway is None:
        print('scipy not installed: skipping ANOVA')
        return 4

    F,p = f_oneway(ctrl, pi8, pi4)
    print(f"ANOVA: F={F}, p={p}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
