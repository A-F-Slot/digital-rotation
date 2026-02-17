# ENGINE_INTEGRATION (v6.2 engine)

This kit currently contains a runner scaffold that demonstrates the output contract.

To make it "true baseline v6.2", integrate the original v6.2 digital rotation engine.

## Expected integration approach
- Replace the synthetic generator block in `run_experiment.py` with a call into the v6.2 engine.
- Keep the output contract unchanged: `paper_ready/` must be produced.

## If you have the engine archive
Preferred formats for integration here:
- .zip
- .tar.gz

RAR (.rar) requires an external extractor (unrar/7z). If your engine is currently packaged as RAR,
re-pack it to ZIP and drop it into this kit under `engine/` (or provide a path), then wire the import.

## Baseline parameter lock
- n=512, replicates=120, seed=42, band=0.08, lambda_threshold=0.75


GitHub:
- v6.2 path: https://github.com/A-F-Slot/digital-rotation/tree/main/V6-2
- v6.2.S path: https://github.com/A-F-Slot/digital-rotation/tree/main/V6-2-S
