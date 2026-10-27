# clear: clean renders of all 40 PHB runs

Pure configuration renders (starting and last configuration) of every PHB run in `manifest.json`, one subfolder per run with four PNGs and a per-run README. All images are completely free of text, legends, axes, titles and periodic box: white background, isometric orthographic view of the whole configuration, 3200x2400 px.

## Images (per run folder)

- `<run>_initial_ball.png` / `<run>_final_ball.png` — ppview ball model (cores and arm beads as spheres).
- `<run>_initial_ballstick.png` / `<run>_final_ballstick.png` — ball-and-stick (core balls; arm joint balls joined by sticks).
- Colours: cores grey, arms slate; each core patch coloured by interaction colour id — a complementary pair (c, -c) shares one colour, so bonded cores show matching patches where they touch. Hue keyed on |c| mod 500; darker variant marks |c| >= 500 (strong channels).

## System and analysis

PHB: patchy helix-bundle molecules, each an icosahedral core (radius 1) carrying three helix arms of five beads (radius 0.1). Arms bind cores through complementary patches. Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

Per-run analysis (in each folder README, computed by `scripts/cluster_labels.py`): bonds are complementary patches on different molecules with patch distance < 0.3 (minimum image); molecule bond graph gives the largest cluster, cluster count, mean valence (max 6), six-valent fraction, and intact tetrahedra per molecule (4-cliques; ideal crystal: 0.358 tetra/mol, six-valent 100%).

## Results at the last configuration

| run | label | molecules | last step | largest cluster | clusters | mean valence | six-valent | tetra/mol |
|---|---|---|---|---|---|---|---|---|
| 2sp_3H3L_T0.078 | 2-species 3H3L, T=0.078 | 500 | 1.655e+09 | 100.0% | 1 | 4.14 | 8.2% | 0.046 |
| 2sp_3H3L_T0.140 | 2-species 3-3 (3 strong + 3 weak), T=0.14 | 500 | 1.895e+09 | 100.0% | 1 | 4.33 | 13.0% | 0.060 |
| 2sp_5H1L_T0.140 | 2-species 5-1 (5 strong + 1 weak), T=0.14 | 500 | 2.124e+09 | 100.0% | 1 | 4.19 | 10.0% | 0.028 |
| 2sp_5L1H_T0.078 | 2-species 5L1H, T=0.078 | 500 | 1.981e+09 | 100.0% | 1 | 4.07 | 6.0% | 0.032 |
| 2sp_5L1H_T0.140 | 2-species 1-5 (1 strong + 5 weak), T=0.14 | 500 | 1.749e+09 | 99.8% | 1 | 4.36 | 15.6% | 0.058 |
| 2sp_equal_T0.140 | 2-species equal (6 strong), T=0.14 | 500 | 1.805e+09 | 100.0% | 1 | 4.10 | 6.2% | 0.044 |
| 2sp_highT_3H3L_T0.150 | 2-species 3H3L, T=0.150, 32-molecule seed | 500 | 2e+09 | 100.0% | 1 | 4.17 | 10.4% | 0.036 |
| 2sp_highT_3H3L_T0.160 | 2-species 3H3L, T=0.160, 32-molecule seed | 500 | 2e+09 | 100.0% | 1 | 4.03 | 6.8% | 0.034 |
| 2sp_highT_3H3L_T0.170 | 2-species 3H3L, T=0.170, 32-molecule seed | 500 | 2e+09 | 100.0% | 1 | 3.75 | 3.8% | 0.016 |
| 2sp_highT_3H3L_T0.180 | 2-species 3H3L, T=0.180, 32-molecule seed | 500 | 2e+09 | 100.0% | 1 | 3.52 | 3.0% | 0.018 |
| 2sp_highT_5L1H_T0.150 | 2-species 5L1H, T=0.150, 32-molecule seed | 500 | 2e+09 | 96.6% | 3 | 3.84 | 9.6% | 0.028 |
| 2sp_highT_5L1H_T0.160 | 2-species 5L1H, T=0.160, 32-molecule seed | 500 | 2e+09 | 91.2% | 5 | 3.22 | 3.6% | 0.028 |
| 2sp_highT_5L1H_T0.170 | 2-species 5L1H, T=0.170, 32-molecule seed | 500 | 2e+09 | 74.4% | 10 | 1.88 | 0.0% | 0.002 |
| 2sp_highT_5L1H_T0.180 | 2-species 5L1H, T=0.180, 32-molecule seed | 500 | 2e+09 | 67.0% | 14 | 1.48 | 0.0% | 0.000 |
| 4sp_seed8_ws_T0.140 | 4-species weak-strong, 8-seed, T=0.14 | 500 | 1.578e+09 | 100.0% | 1 | 4.06 | 10.0% | 0.112 |
| 4sp_ws_T0.140 | 4-species weak-strong (K~101), T=0.14, 32-seed | 500 | 3.675e+08 | 100.0% | 1 | 4.12 | 9.2% | 0.086 |
| 4sp_ww_T0.078 | 4-species weak-weak (K=2), T=0.078, 32-seed | 500 | 1.5e+09 | 100.0% | 1 | 4.08 | 10.0% | 0.112 |
| 4sp_ww_T0.140 | 4-species weak-weak (K=2), T=0.14, 32-seed | 500 | 1.5e+09 | 96.4% | 3 | 4.65 | 43.8% | 0.282 |
| Ka1000_a0.10 | Ka=1000, alpha=0.10 | 500 | 2.695e+09 | 97.4% | 1 | 4.58 | 41.8% | 0.310 |
| Ka1000_a0.12 | Ka=1000, alpha=0.12 | 500 | 2.324e+09 | 98.8% | 1 | 4.60 | 38.8% | 0.310 |
| Ka100_a0.10 | Ka=100, alpha=0.10 | 500 | 3.263e+09 | 98.0% | 1 | 4.70 | 45.0% | 0.322 |
| Ka100_a0.12 | Ka=100, alpha=0.12 | 500 | 3.163e+09 | 99.4% | 1 | 4.65 | 40.0% | 0.312 |
| Ka10_a0.10 | Ka=10, alpha=0.10 | 500 | 3.249e+09 | 97.8% | 1 | 4.74 | 47.2% | 0.342 |
| Ka10_a0.12 | Ka=10, alpha=0.12 | 500 | 3.328e+09 | 99.6% | 1 | 4.64 | 42.2% | 0.326 |
| Ka300_a0.12 | Ka=300, alpha=0.12 | 500 | 3.191e+09 | 98.4% | 1 | 4.53 | 38.0% | 0.304 |
| Ka30_a0.10 | Ka=30, alpha=0.10 | 500 | 3.246e+09 | 97.0% | 3 | 4.62 | 45.0% | 0.326 |
| Ka30_a0.12 | Ka=30, alpha=0.12 | 500 | 3.341e+09 | 99.4% | 1 | 4.68 | 41.2% | 0.308 |
| crystal_Kb1_T0.100 | pre-formed crystal, weak-weak K=2, Kb=1, T=0.10 | 2048 | 1.5e+09 | 73.0% | 28 | 4.79 | 63.4% | 0.372 |
| crystal_Kb300_T0.100 | pre-formed crystal, weak-weak K=2, Kb=300, T=0.10 | 2048 | 1.686e+09 | 73.4% | 29 | 4.80 | 63.8% | 0.374 |
| seed_S128_T0.140_r2 | seed 128 molecules, T=0.140 | 500 | 2.216e+09 | 97.2% | 3 | 4.60 | 44.8% | 0.318 |
| seed_S128_T0.150 | seed 128 molecules, T=0.150 | 500 | 2.341e+09 | 73.6% | 16 | 3.71 | 39.0% | 0.260 |
| seed_S128_T0.160 | seed 128 molecules, T=0.160 | 500 | 8e+08 | 2.2% | 81 | 0.70 | 0.0% | 0.006 |
| seed_S192_T0.140_r1 | seed 192 molecules, T=0.140 | 500 | 3.072e+09 | 97.6% | 1 | 4.71 | 48.4% | 0.342 |
| seed_S256_T0.140_r1 | seed 256 molecules, T=0.140 | 500 | 3.05e+09 | 98.8% | 1 | 4.84 | 51.6% | 0.352 |
| seed_S256_T0.140_r2 | seed 256 molecules, T=0.140 | 500 | 3.035e+09 | 97.8% | 2 | 4.86 | 52.2% | 0.354 |
| seed_S32_T0.150 | seed 32 molecules, T=0.150 | 500 | 8e+08 | 26.4% | 54 | 2.12 | 5.8% | 0.094 |
| seed_S64_T0.140 | seed 64 molecules, T=0.140 | 500 | 2.308e+09 | 93.6% | 2 | 4.14 | 34.6% | 0.270 |
| seed_S8_T0.140 | seed 8 molecules, T=0.140 | 500 | 2.261e+09 | 94.8% | 1 | 4.08 | 29.8% | 0.258 |
| seed_S8_T0.160 | seed 8 molecules, T=0.160 | 500 | 8e+08 | 1.6% | 80 | 0.64 | 0.2% | 0.004 |
| window_Q_T0.140 | melt at T=0.17 then hold T=0.14 | 500 | 2.327e+09 | 94.4% | 3 | 4.08 | 31.0% | 0.272 |

See each run folder README for the starting-configuration row, simulation parameters (`input`, `stages.txt`, `meta.json`), box size and file paths.

## Regenerate

```
python clear/render_clear.py run <name>   # one run (4 PNGs + README)
python clear/render_clear.py all -j 12   # all 40 runs
```
Driver: `render_clear.py`; rasteriser: `../render_phb.py`; analysis: `scripts/cluster_labels.py` (needs numpy, scipy, PIL). Run directories live under `/scratch/sroy85/Github/dna/large_crystal/hand5/` (see `manifest.json`); rendering must run on a machine where that tree exists.
