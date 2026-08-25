# Experiments

Major results must be produced by versioned scripts and summarized by tracked run manifests. Raw run
directories, generated images and checkpoints should remain outside Git; commit only reviewed manifests,
metrics summaries, failure indexes and reports that do not contain restricted data.

Every run manifest must identify its git commit, branch, track, config, dataset manifest, input/output
artifacts, evidence type, limitations and next actions. A run without explicit limitations is invalid.

Generate a Markdown report with:

```powershell
python scripts/generate_report.py experiments/run_manifest.example.json `
  --output outputs/example_run_report.md
```
