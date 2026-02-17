#!/usr/bin/env python3
import sys
import json
from pathlib import Path

REQUIRED = [
    "verdict_details.json",
    "run_manifest.json",
    "hashes.txt",
    "tables/fit_summary_by_condition.csv",
]

EXPECTED_CONDITIONS = [
    "coherent_bin_clean",
    "random_bin",
    "palindrome_bin_no_coherence",
]

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def main():
    if len(sys.argv) != 2:
        print("Usage: python tools/check_official_replication.py <paper_ready_dir>")
        return 2

    base = Path(sys.argv[1]).resolve()
    if not base.exists() or not base.is_dir():
        print("NOT_COMPARABLE (paper_ready directory not found)")
        return 1

    missing = []
    for rel in REQUIRED:
        if not (base / rel).exists():
            missing.append(rel)

    if missing:
        print("NOT_COMPARABLE (missing required files):")
        for m in missing:
            print(f" - {m}")
        return 1

    # Verdict details
    verdict_path = base / "verdict_details.json"
    try:
        verdict = json.loads(read_text(verdict_path))
    except Exception as e:
        print(f"NOT_COMPARABLE (cannot parse verdict_details.json): {e}")
        return 1

    # Attempt to extract status field (we accept a few possible keys)
    status = (
        verdict.get("status")
        or verdict.get("verdict")
        or verdict.get("overall")
        or verdict.get("result")
    )
    if not status:
        print("NOT_COMPARABLE (no status/verdict field in verdict_details.json)")
        return 1

    # CSV condition presence check (lightweight)
    csv_path = base / "tables/fit_summary_by_condition.csv"
    csv_text = read_text(csv_path)
    for cond in EXPECTED_CONDITIONS:
        if cond not in csv_text:
            print(f"NOT_COMPARABLE (missing condition in fit_summary_by_condition.csv): {cond}")
            return 1

    s = str(status).upper()
    if "PASS" in s:
        print("OFFICIAL_REPLICATION_PASS")
        return 0
    if "FAIL" in s:
        print("OFFICIAL_REPLICATION_FAIL")
        return 0

    # Unknown but still official-comparable (files exist, conditions present)
    print(f"OFFICIAL_REPLICATION (status={status})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
