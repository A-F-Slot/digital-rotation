# TROUBLESHOOTING (Top 10)

1) Python not found
- Install Python 3.11+ and ensure `python` is on PATH.

2) Permission denied (Mac/Linux)
- Run: `chmod +x run.sh`

3) PowerShell execution policy blocks scripts
- Run PowerShell:
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

4) pip install fails
- Re-run; if corporate proxy: set proxy env vars.

5) Missing compiler / wheels
- Use Python 3.11/3.12 and avoid exotic platforms.

6) No figures produced
- Check `paper_ready/run_manifest.json` for FAIL reasons.

7) PASS/FAIL confusion
- Read `paper_ready/verdict.txt` (it states thresholds used).

8) Slow runtime
- Lower replicates or n for a quick smoke test.

9) CSV encoding issues
- Ensure UTF-8.

10) Still stuck
- Open an issue and attach `paper_ready/run_manifest.json` + `paper_ready/hashes.txt`.
