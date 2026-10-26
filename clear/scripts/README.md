# scripts

Scripts that produced the PHB visuals (copied from `large_crystal/hand5/final_report/` of the PHB simulation project, as of 2026-10-26). They are kept here as a record; they refer to absolute paths on the ASU Phoenix cluster.

| script | role |
|---|---|
| `cluster_labels.py` | bond detection, clusters, valence, tetrahedra for PHB configurations. Used by `../render_clear.py`. |
| `make_visuals.py` | run registry (the 40 PHB runs) and the 2026-10-23 deliverables: `.mgl` files, annotated images, montages, videos, metrics |
| `render_species.py` | species/cluster-coloured renders built on `../../render_phb.py` |
| `make_videos.py`, `visuals_analysis.py`, `visuals_readme.py` | videos, analysis figures and README of the 2026-10-23 set |
| `param_run_make_renders.py`, `two_species_best_renders.py`, `srv2_render_patchyshape.py` | renders for the parameter-study, two-species and patchy-shape reports |
| `stills.slurm`, `turn.slurm`, `videos.slurm` | Slurm scripts used for the above |

The clean figures in `../<run>/` are made by `../render_clear.py` (see `../README.md`).
