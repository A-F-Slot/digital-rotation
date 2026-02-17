"""
GTUD v6.2.S student runner (v6.2 engine integrated)

Verdict logic (combined):
A) Reference-matching for baseline: coherent_bin_clean metrics must fall within tolerances of the bundled v6.2 reference outputs.
B) Multi-condition falsification: negative controls must fail (random_bin and palindrome_bin_no_coherence).

This yields a student-proof, auditable, falsifiable/verifiable PASS/FAIL.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

KIT_VERSION = "6.2.S"
DOIS = {
    "v6.1_rerelease": "10.5281/zenodo.18452987",
    "v6.2_experiment": "10.5281/zenodo.18453525",
    "v6.16": "10.5281/zenodo.17299194",
    "v6.2S_student_kit": "10.5281/zenodo.18665841",
}

REPO_BASE = "https://github.com/A-F-Slot/digital-rotation"
REPO_PATH_V62 = REPO_BASE + "/tree/main/V6-2"
REPO_PATH_V62S = REPO_BASE + "/tree/main/V6-2-S"

# Tolerances for reference-matching (choose conservative, student-proof)
TOL = {
    "R2_mean_abs": 0.05,               # absolute tolerance
    "R2_std_abs": 0.03,                # absolute tolerance
    "beta_origin_mean_rel": 0.12,      # relative tolerance (12%)
    "R2_origin_mean_abs": 0.20,        # absolute tolerance (origin fits are noisier)
}

# Negative controls must "fail" clearly
NEG_CONTROL = {
    "R2_mean_max": 0.20,               # if control R2_mean > 0.20, it is suspiciously "good"
    "R2_origin_mean_max": 0.20,
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_dirs(out: Path):
    (out / "figures").mkdir(parents=True, exist_ok=True)
    (out / "tables").mkdir(parents=True, exist_ok=True)

def run_v6_2_engine(root: Path) -> Path:
    vendor = root / "vendor" / "v6_2_artifact_pack"
    code = vendor / "code" / "run_v6_2_experiment.py"
    if not code.exists():
        raise FileNotFoundError(f"Missing v6.2 engine at: {code}")

    proc = subprocess.run([sys.executable, str(code)], cwd=str(vendor), capture_output=True, text=True)

    out = root / "paper_ready"
    out.mkdir(parents=True, exist_ok=True)
    (out / "engine_stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (out / "engine_stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError("v6.2 engine execution failed. See paper_ready/engine_stderr.txt")

    return vendor

def copy_outputs(root: Path, vendor: Path):
    out = root / "paper_ready"
    ensure_dirs(out)

    fig_src = vendor / "figures"
    res_src = vendor / "results"
    man_src = vendor / "manifests"
    log_src = vendor / "logs"

    if fig_src.exists():
        for p in fig_src.glob("*.png"):
            shutil.copy2(p, out / "figures" / p.name)

    if res_src.exists():
        for p in res_src.glob("*.csv"):
            shutil.copy2(p, out / "tables" / p.name)

    support = out / "support"
    support.mkdir(parents=True, exist_ok=True)
    for src in [man_src, log_src]:
        if src.exists():
            dst = support / src.name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

def load_fit_summary(out: Path):
    import pandas as pd
    p = out / "tables" / "fit_summary_by_condition.csv"
    if not p.exists():
        raise FileNotFoundError("Missing fit_summary_by_condition.csv in paper_ready/tables/")
    return pd.read_csv(p)

def load_reference(root: Path):
    refp = root / "reference_metrics_v6_2.json"
    if not refp.exists():
        raise FileNotFoundError("Missing reference_metrics_v6_2.json")
    return json.loads(refp.read_text(encoding="utf-8"))

def within(val, ref, abs_tol=None, rel_tol=None):
    if abs_tol is not None:
        return abs(float(val) - float(ref)) <= abs_tol
    if rel_tol is not None:
        r = float(ref)
        if r == 0:
            return abs(float(val)) <= rel_tol
        return abs(float(val) - r) / abs(r) <= rel_tol
    raise ValueError("Need abs_tol or rel_tol")

def compute_verdict(root: Path):
    out = root / "paper_ready"
    df = load_fit_summary(out)
    ref = load_reference(root)

    def row(cond):
        r = df[df["condition"] == cond]
        if len(r) != 1:
            raise ValueError(f"Condition not found or ambiguous: {cond}")
        return r.iloc[0].to_dict()

    clean = row("coherent_bin_clean")
    rand = row("random_bin")
    pal = row("palindrome_bin_no_coherence")

    ref_clean = ref["coherent_bin_clean"]

    checks = []

    # A) Reference-matching (verification)
    checks.append(("clean.R2_mean", within(clean["R2_mean"], ref_clean["R2_mean"], abs_tol=TOL["R2_mean_abs"])))
    checks.append(("clean.R2_std", within(clean["R2_std"], ref_clean["R2_std"], abs_tol=TOL["R2_std_abs"])))
    checks.append(("clean.beta_origin_mean", within(clean["beta_origin_mean"], ref_clean["beta_origin_mean"], rel_tol=TOL["beta_origin_mean_rel"])))
    checks.append(("clean.R2_origin_mean", within(clean["R2_origin_mean"], ref_clean["R2_origin_mean"], abs_tol=TOL["R2_origin_mean_abs"])))

    # B) Negative controls must fail (falsification guardrail)
    checks.append(("random.R2_mean_fail", float(rand["R2_mean"]) <= NEG_CONTROL["R2_mean_max"]))
    checks.append(("random.R2_origin_mean_fail", float(rand["R2_origin_mean"]) <= NEG_CONTROL["R2_origin_mean_max"]))
    checks.append(("palindrome.R2_mean_fail", float(pal["R2_mean"]) <= NEG_CONTROL["R2_mean_max"]))
    checks.append(("palindrome.R2_origin_mean_fail", float(pal["R2_origin_mean"]) <= NEG_CONTROL["R2_origin_mean_max"]))

    passed = all(ok for _, ok in checks)

    details = {
        "verdict": "PASS" if passed else "FAIL",
        "tolerances": {"TOL": TOL, "NEG_CONTROL": NEG_CONTROL},
        "dois": DOIS,
        "repo": {"base": REPO_BASE, "v6.2": REPO_PATH_V62, "v6.2.S": REPO_PATH_V62S},
        "checks": [{"name": n, "ok": bool(ok)} for n, ok in checks],
        "measured": {"coherent_bin_clean": clean, "random_bin": rand, "palindrome_bin_no_coherence": pal},
        "reference": {"coherent_bin_clean": ref_clean},
    }

    (out / "verdict.txt").write_text(details["verdict"] + "\n", encoding="utf-8")
    (out / "verdict_details.json").write_text(json.dumps(details, indent=2), encoding="utf-8")

    return details

def write_methods_results(root: Path, verdict_details: dict):
    out = root / "paper_ready"
    (out / "run_manifest.json").write_text(json.dumps({
        "kit_version": KIT_VERSION,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "engine": "GTUD Digital Rotation v6.2 (bundled artifact pack)",
        "dois": {k: f"https://doi.org/{v}" for k,v in DOIS.items()},
        "repo": {"base": REPO_BASE, "v6.2": REPO_PATH_V62, "v6.2.S": REPO_PATH_V62S},
        "scope": "Digital instantiation replication/robustness suite; not direct physical confirmation.",
        "verdict": verdict_details["verdict"],
    }, indent=2), encoding="utf-8")

    (out / "citation_block.txt").write_text(
        "APA:\n"
        f"Slot, A. F. (2026). GTUD Digital Rotation experiment v6.2: Experimental Validation Package. https://doi.org/{DOIS['v6.2_experiment']}\n"
        f"Slot, A. F. (2026). GTUD v6.16: Time as Rotation Field and Quadratic Torsion in the Digital Domain. https://doi.org/{DOIS['v6.16']}\n"
        f"Slot, A. F. (2026). GTUD Digital Rotation v6.2.S: Student Replication and Extension Suite. https://doi.org/{DOIS['v6.2S_student_kit']}\n"
        "\nGitHub:\n"
        f"v6.2 code path: {REPO_PATH_V62}\n"
        f"v6.2.S kit path: {REPO_PATH_V62S}\n",
        encoding="utf-8",
    )

    (out / "methods_ready.md").write_text(
        "Methods (v6.2.S): This replication runs the authentic GTUD Digital Rotation v6.2 experiment\n"
        f"(DOI: https://doi.org/{DOIS['v6.2_experiment']}) and packages outputs for student publication.\n"
        "Core parameters (per v6.2): n=512; replicates=120; seed=42; band=0.08; lambda_threshold=0.75.\n"
        "Quality gate (per v6.2 code): lambda_threshold=0.75, mean_abs_max=0.10, sign_changes in [2,200].\n"
        "Verdict rule: combined (A) reference-matching for coherent_bin_clean + (B) negative controls must fail.\n",
        encoding="utf-8",
    )

    (out / "results_ready.md").write_text(
        "Results (v6.2.S): Canonical v6.2 figures and tables were generated and are available in paper_ready/.\n"
        f"Verdict: {verdict_details['verdict']}.\n"
        "See paper_ready/verdict_details.json for measured values, tolerances, and control checks.\n",
        encoding="utf-8",
    )

def write_hashes(root: Path):
    out = root / "paper_ready"
    hashes = []
    for p in sorted([p for p in out.rglob("*") if p.is_file()]):
        hashes.append(f"{p.relative_to(out)}  {sha256_file(p)}")
    (out / "hashes.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")

def main():
    root = Path(__file__).resolve().parent
    vendor = run_v6_2_engine(root)
    copy_outputs(root, vendor)
    details = compute_verdict(root)
    write_methods_results(root, details)
    write_hashes(root)
    print("Done. See paper_ready/")

if __name__ == "__main__":
    main()
