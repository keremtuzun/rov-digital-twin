# Inspection/failure twin MVP specification

The failure twin is controlled data infrastructure for research. It is separate from Unity navigation
physics and does not claim physically calibrated damage rendering.

`oceansense.failure_twin` generates seeded normal/degraded pairs for pipes, welds, joints, plates,
cables, supports and concrete piers. Supported controlled conditions include corrosion, cracks, coating
loss, deformation, biofouling, sediment coverage and leak-like visual anomalies. Each example includes:

- normal image and degraded image;
- pixel mask and severity ordinal;
- structure/material/defect/pattern fields;
- turbidity, lighting, blur, backscatter, occlusion, viewpoint and distance metadata;
- stable scenario ID, seed and leakage-resistant split;
- natural-language caption and an explicit synthetic evidence boundary.

Run:

```powershell
python scripts/run_failure_twin_batch.py --config config/failure_twin_mvp.json `
  --output outputs/failure_twin_mvp
```

The default config emits 100 paired scenarios. Before using a batch, verify metadata completeness,
deterministic regeneration, split isolation and human visual sanity. Synthetic results must be reported
separately from real inspection data and cannot establish real-world accuracy or physical severity.
