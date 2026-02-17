#!/usr/bin/env python3
"""Generate GTUD Digital Rotation v6.2 experiment artifacts.

This generator is deterministic given the RNG seed.

Artifacts written:
  data/raw_v6_2_all_conditions.csv
  data/fit_v6_2_per_replicate.csv
  results/summary_by_condition_and_k.csv
  results/fit_summary_by_condition.csv
  logs/runlog_v6_2.txt

Pre-registered acceptance (outcome-agnostic):
  (1) low-frequency energy ratio lambda >= lambda_threshold for |f|<=band
  (2) |mean(x)| <= mean_abs_max
  (3) sign changes in x[0:n/2] within [sign_changes_min, sign_changes_max]

Quadraticity score Q (R^2) is reported, NOT used for selection.
"""

from __future__ import annotations

import argparse
import math
import os
import platform
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Params:
    n: int = 512
    replicates: int = 120
    seed: int = 42
    band: float = 0.08
    lambda_threshold: float = 0.75
    mean_abs_max: float = 0.10
    sign_changes_min: int = 2
    sign_changes_max: int = 200
    p_spectrum: float = 2.70  # controls effective beta via sum(w f^2)


def unit_rms(x: np.ndarray) -> np.ndarray:
    x = x - float(np.mean(x))
    rms = float(np.sqrt(np.mean(x * x)))
    if rms == 0:
        return x
    return x / rms


def low_freq_ratio(x: np.ndarray, band: float) -> float:
    n = len(x)
    X = np.fft.rfft(x)
    power = (np.abs(X) ** 2)
    freqs = np.fft.rfftfreq(n, d=1.0)
    num = float(power[freqs <= band].sum())
    den = float(power.sum())
    return num / den if den > 0 else 0.0


def sign_changes_half(x: np.ndarray) -> int:
    half = x[: len(x) // 2]
    s = np.sign(half)
    s[s == 0] = 1
    return int(np.sum(s[1:] != s[:-1]))


def generate_coherent_soft(rng: np.random.Generator, p: Params) -> tuple[np.ndarray, dict]:
    """Generate one coherent, palindromized, low-pass real signal x (unit RMS)."""
    n = p.n
    m = n // 2

    # Frequency bins for the half-signal length m
    freqs_m = np.fft.rfftfreq(m, d=1.0)
    idx = np.where((freqs_m > 0) & (freqs_m <= p.band))[0]
    if len(idx) == 0:
        raise RuntimeError("band too small; no frequency bins available")

    while True:
        spec = np.zeros(m // 2 + 1, dtype=np.complex128)
        # Power ~ 1/f^p; amplitude ~ 1/f^(p/2). Use integer bin index as 'f'.
        for k in idx:
            f = float(k)
            amp = 1.0 / (f ** (p.p_spectrum / 2.0))
            phase = rng.uniform(0.0, 2.0 * math.pi)
            spec[k] = amp * (math.cos(phase) + 1j * math.sin(phase))

        # Ensure Nyquist bin is real (if present)
        if m % 2 == 0:
            spec[-1] = complex(spec[-1].real, 0.0)

        h = np.fft.irfft(spec, n=m)
        x = np.concatenate([h, h[::-1]])
        x = unit_rms(x)

        lam = low_freq_ratio(x, p.band)
        mu = float(np.mean(x))
        sc = sign_changes_half(x)

        if (lam >= p.lambda_threshold) and (abs(mu) <= p.mean_abs_max) and (p.sign_changes_min <= sc <= p.sign_changes_max):
            return x.astype(np.float64), {"lambda": lam, "mean": mu, "sign_changes_half": sc}


def to_bin(x: np.ndarray) -> np.ndarray:
    xb = np.where(x >= 0, 1.0, -1.0)
    return xb.astype(np.float64)


def corr_mean(x_ref: np.ndarray, x_other: np.ndarray) -> float:
    return float(np.mean(x_ref * x_other))


def r2_score(y: np.ndarray, yhat: np.ndarray) -> float:
    y = y.astype(np.float64)
    yhat = yhat.astype(np.float64)
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    if ss_tot == 0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def fit_through_origin(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Fit y = beta*x through origin. Returns (beta, R2)."""
    x = x.astype(np.float64)
    y = y.astype(np.float64)
    denom = float(np.dot(x, x))
    beta = float(np.dot(x, y) / denom) if denom != 0 else float("nan")
    yhat = beta * x
    return beta, r2_score(y, yhat)


def fit_with_intercept(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """OLS fit y = a + b*x. Returns (b, a, R2)."""
    x = x.astype(np.float64)
    y = y.astype(np.float64)
    A = np.vstack([x, np.ones_like(x)]).T
    # least squares
    (b, a), *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = b * x + a
    return float(b), float(a), r2_score(y, yhat)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_root", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    args = parser.parse_args()

    p = Params()
    rng = np.random.default_rng(p.seed)

    root = args.out_root
    data_dir = os.path.join(root, "data")
    res_dir = os.path.join(root, "results")
    log_dir = os.path.join(root, "logs")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(res_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # k grid: small-angle <= n/16 plus one out-of-regime point at n/8.
    k_small = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 28, 32]
    k_out = [p.n // 8]  # 64 for n=512
    k_grid = k_small + k_out

    # Conditions
    noise_sigmas = [0.05, 0.10, 0.30]
    bitflip_ps = [0.01, 0.02, 0.05, 0.10]

    rows = []
    coh_rows = []

    # Generate base coherent sequences once per replicate; reuse for several conditions
    for rep in range(p.replicates):
        x, coh = generate_coherent_soft(rng, p)
        xb = to_bin(x)

        coh_rows.append({
            "replicate": rep,
            "lambda": coh["lambda"],
            "mean": coh["mean"],
            "sign_changes_half": coh["sign_changes_half"],
        })

        # coherent_soft (clean)
        for k in k_grid:
            theta = 2.0 * math.pi * k / p.n
            xk = np.roll(x, -k)
            C = corr_mean(x, xk)
            E = 2.0 - 2.0 * C
            rows.append({
                "condition": "coherent_soft",
                "replicate": rep,
                "n": p.n,
                "k": k,
                "theta": theta,
                "theta2": theta * theta,
                "C": C,
                "E": E,
            })

        # coherent_soft + additive noise (robustness proxy)
        for sigma in noise_sigmas:
            cname = f"coherent_soft_noise_sigma{sigma:.2f}"
            for k in k_grid:
                theta = 2.0 * math.pi * k / p.n
                xk = np.roll(x, -k)
                xk_noisy = xk + rng.normal(0.0, sigma, size=p.n)
                xk_noisy = unit_rms(xk_noisy)  # normalization induces E(0) > 0
                C = corr_mean(x, xk_noisy)
                E = 2.0 - 2.0 * C
                rows.append({
                    "condition": cname,
                    "replicate": rep,
                    "n": p.n,
                    "k": k,
                    "theta": theta,
                    "theta2": theta * theta,
                    "C": C,
                    "E": E,
                })

        # coherent_bin
        for k in k_grid:
            theta = 2.0 * math.pi * k / p.n
            xk = np.roll(xb, -k)
            C = corr_mean(xb, xk)
            E = 2.0 - 2.0 * C
            rows.append({
                "condition": "coherent_bin",
                "replicate": rep,
                "n": p.n,
                "k": k,
                "theta": theta,
                "theta2": theta * theta,
                "C": C,
                "E": E,
            })

        # coherent_bin + bitflip corruption
        for prob in bitflip_ps:
            cname = f"coherent_bin_bitflip_p{prob:.2f}"
            for k in k_grid:
                theta = 2.0 * math.pi * k / p.n
                xk = np.roll(xb, -k).copy()
                flips = rng.random(p.n) < prob
                xk[flips] *= -1.0
                C = corr_mean(xb, xk)
                E = 2.0 - 2.0 * C
                rows.append({
                    "condition": cname,
                    "replicate": rep,
                    "n": p.n,
                    "k": k,
                    "theta": theta,
                    "theta2": theta * theta,
                    "C": C,
                    "E": E,
                })

        # Negative controls
        # random_bin
        xrand = rng.choice([-1.0, 1.0], size=p.n)
        for k in k_grid:
            theta = 2.0 * math.pi * k / p.n
            xk = np.roll(xrand, -k)
            C = corr_mean(xrand, xk)
            E = 2.0 - 2.0 * C
            rows.append({
                "condition": "random_bin",
                "replicate": rep,
                "n": p.n,
                "k": k,
                "theta": theta,
                "theta2": theta * theta,
                "C": C,
                "E": E,
            })

        # palindrome_bin_no_coherence
        half = rng.choice([-1.0, 1.0], size=p.n // 2)
        xpal = np.concatenate([half, half[::-1]])
        for k in k_grid:
            theta = 2.0 * math.pi * k / p.n
            xk = np.roll(xpal, -k)
            C = corr_mean(xpal, xk)
            E = 2.0 - 2.0 * C
            rows.append({
                "condition": "palindrome_bin_no_coherence",
                "replicate": rep,
                "n": p.n,
                "k": k,
                "theta": theta,
                "theta2": theta * theta,
                "C": C,
                "E": E,
            })

    df_raw = pd.DataFrame(rows)
    df_coh = pd.DataFrame(coh_rows)

    # Fits per replicate per condition
    fit_rows = []
    conditions = sorted(df_raw["condition"].unique())

    small_mask = df_raw["k"].isin(k_small)

    for cond in conditions:
        dcond = df_raw[df_raw["condition"] == cond]
        for rep in range(p.replicates):
            drep = dcond[dcond["replicate"] == rep].copy()
            drep_small = drep[ drep["k"].isin(k_small) ].sort_values("k")

            x = drep_small["theta2"].to_numpy()
            y = drep_small["E"].to_numpy()

            beta0, r2_0 = fit_through_origin(x, y)
            slope, intercept, r2_lin = fit_with_intercept(x, y)

            # baseline-corrected origin fit for conditions where E(0) is nonzero
            # Use k>0 subset.
            drep_small_pos = drep_small[drep_small["k"] > 0]
            x_pos = drep_small_pos["theta2"].to_numpy()
            E0 = float(drep_small[drep_small["k"] == 0]["E"].iloc[0])
            y_pos = (drep_small_pos["E"].to_numpy() - E0)
            beta_delta, r2_delta = fit_through_origin(x_pos, y_pos)

            fit_rows.append({
                "condition": cond,
                "replicate": rep,
                "beta_origin": beta0,
                "r2_origin": r2_0,
                "slope": slope,
                "intercept": intercept,
                "r2": r2_lin,
                "E0": E0,
                "beta_origin_delta": beta_delta,
                "r2_origin_delta": r2_delta,
            })

    df_fit = pd.DataFrame(fit_rows)

    # Summaries
    df_summary = df_raw.groupby(["condition", "k"], as_index=False).agg(
        theta=("theta", "mean"),
        theta2=("theta2", "mean"),
        C_mean=("C", "mean"),
        C_std=("C", "std"),
        E_mean=("E", "mean"),
        E_std=("E", "std"),
        n_rows=("E", "size"),
    )

    df_fit_summary = df_fit.groupby("condition", as_index=False).agg(
        beta_origin_mean=("beta_origin", "mean"),
        beta_origin_std=("beta_origin", "std"),
        r2_origin_mean=("r2_origin", "mean"),
        r2_origin_std=("r2_origin", "std"),
        slope_mean=("slope", "mean"),
        slope_std=("slope", "std"),
        intercept_mean=("intercept", "mean"),
        intercept_std=("intercept", "std"),
        r2_mean=("r2", "mean"),
        r2_std=("r2", "std"),
        E0_mean=("E0", "mean"),
        E0_std=("E0", "std"),
        beta_origin_delta_mean=("beta_origin_delta", "mean"),
        beta_origin_delta_std=("beta_origin_delta", "std"),
        r2_origin_delta_mean=("r2_origin_delta", "mean"),
        r2_origin_delta_std=("r2_origin_delta", "std"),
    )

    # Write
    raw_path = os.path.join(data_dir, "raw_v6_2_all_conditions.csv")
    fit_path = os.path.join(data_dir, "fit_v6_2_per_replicate.csv")
    summary_path = os.path.join(res_dir, "summary_by_condition_and_k.csv")
    fit_sum_path = os.path.join(res_dir, "fit_summary_by_condition.csv")
    coh_path = os.path.join(data_dir, "coherence_metrics_per_replicate.csv")

    df_raw.to_csv(raw_path, index=False)
    df_fit.to_csv(fit_path, index=False)
    df_summary.to_csv(summary_path, index=False)
    df_fit_summary.to_csv(fit_sum_path, index=False)
    df_coh.to_csv(coh_path, index=False)

    # Runlog
    log_path = os.path.join(log_dir, "runlog_v6_2.txt")
    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "params": p.__dict__,
        "k_small": k_small,
        "k_out": k_out,
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(meta, indent=2, sort_keys=True))
        f.write("\n")

    print("Wrote:")
    print(" ", raw_path)
    print(" ", fit_path)
    print(" ", coh_path)
    print(" ", summary_path)
    print(" ", fit_sum_path)
    print(" ", log_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
