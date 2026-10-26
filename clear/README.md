# clear: clean PHB configuration images

Clean renders (no title, legend, axes or periodic box; white background) of the starting and last configuration of 40 PHB (patchy helix-bundle) simulation runs, for use in figures and grant material. Every run has its own folder `<run>/` holding four PNGs (3200x2400) and a `README.md` that describes the run (parameters, configurations, structure metrics).

| image | what |
|---|---|
| `<run>_initial_ball.png` / `<run>_final_ball.png` | ppview ball model: icosahedral cores and arm beads as spheres, patches coloured by interaction colour |
| `<run>_initial_ballstick.png` / `<run>_final_ballstick.png` | ball-and-stick: cores as balls, each helix arm as small joint balls joined by sticks |

'initial' is the configuration the MD started from (after the short MC relaxation where one was run); 'final' is the run's last written configuration at render time (2026-10-26). Runs marked live in the series notes may have continued since, so rerun `render_clear.py` to refresh. Each view is isometric and orthographic and frames the whole configuration, so a small crystal in a mostly empty box appears small.

## Runs

| run | series | description |
|---|---|---|
| [`2sp_equal_T0.140`](2sp_equal_T0.140/README.md) | 2-species, T = 0.14 | 2-species equal (6 strong), T=0.14 |
| [`2sp_5H1L_T0.140`](2sp_5H1L_T0.140/README.md) | 2-species, T = 0.14 | 2-species 5-1 (5 strong + 1 weak), T=0.14 |
| [`2sp_3H3L_T0.140`](2sp_3H3L_T0.140/README.md) | 2-species, T = 0.14 | 2-species 3-3 (3 strong + 3 weak), T=0.14 |
| [`2sp_5L1H_T0.140`](2sp_5L1H_T0.140/README.md) | 2-species, T = 0.14 | 2-species 1-5 (1 strong + 5 weak), T=0.14 |
| [`2sp_3H3L_T0.078`](2sp_3H3L_T0.078/README.md) | 2-species, T = 0.078 (stopped) | 2-species 3H3L, T=0.078 |
| [`2sp_5L1H_T0.078`](2sp_5L1H_T0.078/README.md) | 2-species, T = 0.078 (stopped) | 2-species 5L1H, T=0.078 |
| [`2sp_highT_3H3L_T0.150`](2sp_highT_3H3L_T0.150/README.md) | 2-species, higher T | 2-species 3H3L, T=0.150, 32-molecule seed |
| [`2sp_highT_3H3L_T0.160`](2sp_highT_3H3L_T0.160/README.md) | 2-species, higher T | 2-species 3H3L, T=0.160, 32-molecule seed |
| [`2sp_highT_3H3L_T0.170`](2sp_highT_3H3L_T0.170/README.md) | 2-species, higher T | 2-species 3H3L, T=0.170, 32-molecule seed |
| [`2sp_highT_3H3L_T0.180`](2sp_highT_3H3L_T0.180/README.md) | 2-species, higher T | 2-species 3H3L, T=0.180, 32-molecule seed |
| [`2sp_highT_5L1H_T0.150`](2sp_highT_5L1H_T0.150/README.md) | 2-species, higher T | 2-species 5L1H, T=0.150, 32-molecule seed |
| [`2sp_highT_5L1H_T0.160`](2sp_highT_5L1H_T0.160/README.md) | 2-species, higher T | 2-species 5L1H, T=0.160, 32-molecule seed |
| [`2sp_highT_5L1H_T0.170`](2sp_highT_5L1H_T0.170/README.md) | 2-species, higher T | 2-species 5L1H, T=0.170, 32-molecule seed |
| [`2sp_highT_5L1H_T0.180`](2sp_highT_5L1H_T0.180/README.md) | 2-species, higher T | 2-species 5L1H, T=0.180, 32-molecule seed |
| [`4sp_ww_T0.140`](4sp_ww_T0.140/README.md) | 4-species preconnected | 4-species weak-weak (K=2), T=0.14, 32-seed |
| [`4sp_ws_T0.140`](4sp_ws_T0.140/README.md) | 4-species preconnected | 4-species weak-strong (K~101), T=0.14, 32-seed |
| [`4sp_ww_T0.078`](4sp_ww_T0.078/README.md) | 4-species preconnected | 4-species weak-weak (K=2), T=0.078, 32-seed |
| [`4sp_seed8_ws_T0.140`](4sp_seed8_ws_T0.140/README.md) | 4-species preconnected | 4-species weak-strong, 8-seed, T=0.14 |
| [`seed_S8_T0.140`](seed_S8_T0.140/README.md) | Seeded growth (4-species, K=2) | seed 8 molecules, T=0.140 |
| [`seed_S8_T0.160`](seed_S8_T0.160/README.md) | Seeded growth (4-species, K=2) | seed 8 molecules, T=0.160 |
| [`seed_S32_T0.150`](seed_S32_T0.150/README.md) | Seeded growth (4-species, K=2) | seed 32 molecules, T=0.150 |
| [`seed_S64_T0.140`](seed_S64_T0.140/README.md) | Seeded growth (4-species, K=2) | seed 64 molecules, T=0.140 |
| [`seed_S128_T0.140_r2`](seed_S128_T0.140_r2/README.md) | Seeded growth (4-species, K=2) | seed 128 molecules, T=0.140 |
| [`seed_S128_T0.150`](seed_S128_T0.150/README.md) | Seeded growth (4-species, K=2) | seed 128 molecules, T=0.150 |
| [`seed_S128_T0.160`](seed_S128_T0.160/README.md) | Seeded growth (4-species, K=2) | seed 128 molecules, T=0.160 |
| [`seed_S192_T0.140_r1`](seed_S192_T0.140_r1/README.md) | Seeded growth (4-species, K=2) | seed 192 molecules, T=0.140 |
| [`seed_S256_T0.140_r1`](seed_S256_T0.140_r1/README.md) | Seeded growth (4-species, K=2) | seed 256 molecules, T=0.140 |
| [`seed_S256_T0.140_r2`](seed_S256_T0.140_r2/README.md) | Seeded growth (4-species, K=2) | seed 256 molecules, T=0.140 |
| [`Ka10_a0.10`](Ka10_a0.10/README.md) | Ka x alpha study (S128, T=0.14) | Ka=10, alpha=0.10 |
| [`Ka10_a0.12`](Ka10_a0.12/README.md) | Ka x alpha study (S128, T=0.14) | Ka=10, alpha=0.12 |
| [`Ka30_a0.10`](Ka30_a0.10/README.md) | Ka x alpha study (S128, T=0.14) | Ka=30, alpha=0.10 |
| [`Ka30_a0.12`](Ka30_a0.12/README.md) | Ka x alpha study (S128, T=0.14) | Ka=30, alpha=0.12 |
| [`Ka100_a0.10`](Ka100_a0.10/README.md) | Ka x alpha study (S128, T=0.14) | Ka=100, alpha=0.10 |
| [`Ka100_a0.12`](Ka100_a0.12/README.md) | Ka x alpha study (S128, T=0.14) | Ka=100, alpha=0.12 |
| [`Ka300_a0.12`](Ka300_a0.12/README.md) | Ka x alpha study (S128, T=0.14) | Ka=300, alpha=0.12 |
| [`Ka1000_a0.10`](Ka1000_a0.10/README.md) | Ka x alpha study (S128, T=0.14) | Ka=1000, alpha=0.10 |
| [`Ka1000_a0.12`](Ka1000_a0.12/README.md) | Ka x alpha study (S128, T=0.14) | Ka=1000, alpha=0.12 |
| [`window_Q_T0.140`](window_Q_T0.140/README.md) | Melt-quench | melt at T=0.17 then hold T=0.14 |
| [`crystal_Kb1_T0.100`](crystal_Kb1_T0.100/README.md) | Pre-formed crystal (2048 molecules) | pre-formed crystal, weak-weak K=2, Kb=1, T=0.10 |
| [`crystal_Kb300_T0.100`](crystal_Kb300_T0.100/README.md) | Pre-formed crystal (2048 molecules) | pre-formed crystal, weak-weak K=2, Kb=300, T=0.10 |

## Files

* `render_clear.py`: renders all runs and writes the per-run READMEs (`python render_clear.py all -j 6`, or `run NAME`). Uses `../render_phb.py` (numpy rasteriser, no GPU or display) and `scripts/cluster_labels.py`.
* `render_all.slurm`: the CPU Slurm job used (about 18 min for all 40 runs).
* `manifest.json` and `manifest_dump.py`: the run registry (topology, starting and last configuration paths per run) and the script that dumped it from `make_visuals.py`.
* `scripts/`: the scripts that made the earlier PHB visuals (2026-10-23), copied for the record; see `scripts/README.md`.

The ball-and-stick model is the `--model ballstick` option added to `../render_phb.py` (`--stick-radius`, `--joint-radius`).
