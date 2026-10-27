# Figure / video generation scripts (archived from `/mnt/Drive/PHB`)

Archived 2026-10-26. Source tree: `/mnt/Drive/PHB` (not a git repo).
Only **code** is archived here — no binaries (no `.png`/`.webm`/`.dat`/`.top`/`.mgl`/`.npy`).

File names are namespaced from their original path: `/` → `__`.
E.g. `PHB5__square__a03__plot.gp` = `/mnt/Drive/PHB/PHB5/square/a03/plot.gp`.

## 1. `gnuplot/` — energy plots (`plot.png`, `histogram.png`, `FloatPerformance.png`)

18 `.gp` files + 4 `plot.sh` generators. Each `.gp` plots `energy.ign`
columns (`u 1:4`) across temperature outputs into a PNG:

| archived file | original | produces (in original dir) |
|---|---|---|
| `PHB5__square__a03__plot.gp` | `PHB5/square/a03/plot.gp` | `PHB5/square/a03/plot.png` |
| `PHB3__square__a1__plot.gp` | `PHB3/square/a1/plot.gp` | `PHB3/square/a1/plot.png` |
| `PHB__Seeded__HandLength__7longHand__plot.gp` | `PHB/Seeded/HandLength/7longHand/plot.gp` | `PHB/Seeded/HandLength/7longHand/plot.png` |
| `PHBdegub__small__gnu.gp` | `PHBdegub/small/gnu.gp` | `PHBdegub/small/histogram.png` |
| `PHBdegub__small1_2__gnu.gp`, `...__gnu2.gp` | `PHBdegub/small1_2/gnu.gp`, `gnu2.gp` | `PHBdegub/small1_2/plot.png` |
| `PHBcg__Performance__float.gp`, `...__mixed.gp` | `PHBcg/Performance/float.gp`, `mixed.gp` | `FloatPerformance.png` / mixed perf plots |
| `Backup__*__plot.gp` (11 files) | `Backup/...` mirrors | corresponding `Backup/.../plot.png` |
| `*__plot.sh` (4 files) | `PHB2/sq0.1/plot.sh`, `Backup/PHB2/a0.1/plot.sh`, `Backup/PHB2/crystal/s1-05/plot.sh`, `Backup/PHB2/crystal/s1/plot.sh` | generate `plot.gp` for a temperature sweep **and** run `terminal autoconvert -i <topology> -d last_conf.dat -o last.mgl` per output dir, then `gnuplot plot.gp` |
| `*__script.sh` (8 files, added 2026-10-27) | `50helix/10/script.sh`, `560helix/10/script.sh`, `PHB/Seeded/HandLength/7longHand/script.sh`, `Backup/PHB4/square/a03/script.sh`, `PHB5/lowa/a03/script.sh`, `PHB5/square/a03/script.sh`, `PHB3/square/a1/script.sh`, `Helix/Single/script.sh` | simulation-run scripts whose tail does the same inline-gnuplot `plot.png` + `terminal autoconvert ... last.mgl` pattern; these are the master templates behind the `plot.png` files in `PHB5/*`, `PHB3/square/a1`, `Seeded/*`, `SmallSeed/*`, `PHB/Seeded/*`, `PHB/SmallSeed/*`, `50helix/*`, `560helix/*`, `Helix/*` (top-level `script.sh` is a symlink to `Backup/PHB4/square/a03/script.sh`) |

Run: `gnuplot <file>.gp` (needs the `output/<T>/energy.ign` tree, not archived).

## 2. `oxdna-angle-analysis/` — oxDNA angle histograms + cluster figures

Matplotlib + scikit-learn + `oxDNA_analysis_tools`, producing
`Plot.png`, `angles.npy`, `k-mean.png`, `fig2.1.png/.svg`, `fig2.2.png`,
`presimu.png`, `BackTo2d.png`, `cluster.png`, `color.png`, `colorbar.png`,
`prespective*.png` under `PHBdna2/simplex/*/output/`.

- `PHBdna2__simplex__5T__output__1__plot.py` — per-replica angle histogram
  family for 5T (representative; identical copies exist in `5T/output/2..6/`).
- `PHBdna2__simplex__5T__output__combined__plot.py` — concatenated-trajectory
  variant (`combined.dat` built by `plot.ipynb` cell 0:
  `for((i=1;i<=6;i++)); do cat ../$i/trajectory.dat >> combined.dat; done`).
- Same pattern for `10T` / `15T` / `20T` families (helix/edge index lists differ
  per temperature; `10T` additionally has `plot1.py`–`plot6.py` per-replica
  splits + `plottemp.py`).
- `PHBdna2__simplex__5T__output__analysis4-mean__kmean.py` /
  `__kmeanMulti.py` — KMeans 3D→2D fitting sweep (multiplier 3.0–3.5, 50 steps)
  behind `BackTo2d.png`, `cluster.png`, `k-mean.png`, `presimu.png`.
- `PHBdna2__simplex__5T__output__combined__plot.ipynb`,
  `PHBdna2__simplex__15T__output__combined__plot.ipynb` — as-original
  notebooks (small, outputs kept).
- `PHBdna2__simplex__5T__output__analysis4-mean__a4mean.cleared.ipynb` +
  `...__a4mean.code.py` — the 33-cell `a4mean.ipynb` with all cell outputs
  stripped (original is ~20 MB with embedded figures at
  `PHBdna2/simplex/5T/output/analysis4-mean/a4mean.ipynb`; the `.code.py` is a
  plain-text export of its code cells). Covers rotational correction
  (`planeFit`/`rotateEuler`), KMeans (8 and 12 clusters), SVD superimposition
  over 8! permutations, and `fig2.1.svg`, `fig2.2.png`, `2dfitting.dat` output.

Dependencies (not archived): `oxDNA_analysis_tools`, `numpy`, `matplotlib`,
`pandas`, `scikit-learn`, `biopython`, `plotly`, `scipy`, `tqdm`.

## 3. `mgl-generation/` — `.mgl` files for ppview/cogli2 viewing

- `mgl_files__README.md` — 14-crystal table + generation command:
  `~/Documents/Github/oxDNAcpp/main/src/build/terminal phbcluster -i <topology.phb> -d <final_conf.dat> -o <out>.mgl --patchRadius 0.3`
  (renders in ppview or `~/Documents/Software/cogli2/build/bin/cogli2`).
- `mgl_files__archive__README.md` — 11 archive-crystal table, same command.
- The `plot.sh` / `*__script.sh` files in `gnuplot/` also show the per-frame variant:
  `terminal autoconvert -i <topology> -d last_conf.dat -o last.mgl`.
  The same 2-line `rm -rf last.mgl && terminal autoconvert ... &` snippet recurs in
  `Backup/PHB/s2helix/resume.sh`, `Backup/PHB/sh0ab100/resume.sh`,
  `Backup/PHB/sh0alpha0.05/resume.sh`, `PHBdegub/small/resume.sh`,
  `PHBdegub/small0.01/resume.sh` (simulation-resume scripts; pattern already
  archived, not copied one by one).
- `clusters__run_analysis.sh` (added 2026-10-27) — batch driver that walks every
  `*.phb` under `/mnt/Drive/PHB` (excluding `Backup/`, `PHB/PHB/`) and runs
  `analyze_crystal.py --format phb --cutoff 0.20 --mgl --mgl-out ... --json-out ...`
  to produce one `<label>.mgl` + `<label>.json` per simulation in
  `/mnt/Drive/PHB/clusters/` (the `.mgl`/`.json` pairs rendered by ppview).
- `oxDNAcpp__pyrochlore__analyze_crystal.py` (added 2026-10-27) — the crystal
  quality analyzer itself (distance/orientation binding detection, modulo-500
  colour rule, `--cutoff 0.20` for PHB). Pinned copy from
  `git@github.com:Subhajit-Roy-Partho/oxDNAcpp.git` at commit `56fc569`
  (`pyrochlore/analyze_crystal.py`); canonical source lives in that repo, this
  copy freezes the version that generated the current `clusters/` outputs.

`.mgl` binaries themselves live in `/mnt/Drive/PHB/mgl_files/` (14 files),
`/mnt/Drive/PHB/mgl_files/archive/` (11 files), `/mnt/Drive/PHB/clusters/`
(~23 MB) and scattered `last.mgl` outputs — none archived here.

## 4. Trajectory videos — no generating script found (gap)

`PHBdna2/simplex/5T/output/Figures/` contains `traj1.png`–`traj13.png`,
`cluster.png`, `clusterPresimulated.png`, `trajectory12fps.webm` (143 MB),
`trajectory24fps.webm` (11 MB). A full-directory grep for
`ffmpeg`/`FuncAnimation`/`VideoWriter`/`imageio`/`cv2` over
`*.py`/`*.ipynb`/`*.sh` found no generating script — these were most likely
captured manually (ppview `P`-key screenshots / `cli/generate-image.js`,
oxView screen recording, or a screen recorder). To reproduce with ppview:

```sh
node cli/generate-image.js --top <topology.top> --traj <trajectory.dat> \
  --frame <n> -o traj<n>.png --width 1920 --height 1080
```

(see `cli/generate-image.js --help`). If the original capture command is
identified later, add it here.

## 5. Full-tree re-audit 2026-10-27 — remaining items with no generator in tree

Re-scanned all of `/mnt/Drive/PHB` (all `*.py`/`*.ipynb`/`*.gp`/`*.sh`, plus a
check for Chimera/VMD/PyMOL/Blender/POV-Ray scripts — none exist). 108 PNGs +
1 SVG + 2 `.webm` inventoried; everything else maps to sections 1–4 above.
No generating code was found for:

- `magic/largeSquare/4x4cross-section.png`, `magic/round/hollow.png`,
  `magic/round4/round4.png` — almost certainly manual screenshots; no script.
- `PHB/60helix/10/output/all/dev_rmsd.png` — no `dev_rmsd` generator script.
- `PHBdna2/duplex/5T/output/1/rmsf_rmsd.png` — no `rmsf` generator script.
- `PHBdna2/simplex/10T/output/combined/barchart.png` — no `barchart` script.
- `PHB5/square/a1/plotBack.png`, `PHB5/lowa/a03/s2plot.png` — one-off variants
  of the §1 inline-gnuplot runs (tweaked replot, command not saved).
- `PHBdna2/simplex/5T/output/Figures/traj*.png`, `cluster*.png`,
  `trajectory12fps.webm`, `trajectory24fps.webm` — see §4.

ppview-side renderers that reproduce this class of output headlessly
(`render_phb.py`, `render_batch.py`, `cli/generate-image.js`, `bench/`,
`visual-tests/`) are tracked in this repo outside `analysis-scripts/`.

## 6. Drive-wide coverage pass 2026-10-26 (`drive-coverage/` + images in place)

Audit of `/mnt/Drive/PHB`: 214 sweep dirs (`output/` parents), 1471 `last_conf.dat`
(~89% completed, t>0), 1471 trajectories. Before the pass, 116 sweeps had no image
at all. Scripts (all idempotent, repo-convention outputs written in place):

- `gen_missing_plots.py` — wrote 65 missing energy `plot.png` (+ `plot.gp`) in the
  repo's gnuplot style (`u 1:4`, log x): 13 PHBdegub + 2 PHBcg/PHBlb + 45 helix
  (50helix/60helix/560helix scans + PHB/ mirrors + Helix/Single) +
  5 PHBdna2 (duplex 10/15/20T, simplex 15/20T). Backup/ mirrors intentionally skipped.
- `fill_clusters.sh` — parallel form of `clusters/run_analysis.sh`; verified
  `clusters/` now holds `.mgl`+`.json` for all 869 processable completed runs
  (18 dirs have empty N_conf=0 confs — simulations never ran — correctly skipped).
- `render_finals.sh` — text-free `final.png` per completed run dir via
  `render_phb.py` (`--model ball`, 1920x1080, white, no title/legend/box):
  same clear/ image conventions for the PHB-format runs.
- `clear/scripts/yield_scan.py` (canonical version by the parallel session; runs on
  `/scratch`, needs numpy/scipy) — yield of every `final_conf.dat`: largest cluster,
  six-valent fraction, tetrahedra/molecule into `yield.csv`. NOTE: the
  `assembled_percentage` in `clusters/*.json` is uniformly 0.0 on this drive (tool
  definition mismatch), so hero selection instead uses `yield_drive.py` (same real
  yield metrics via `clear/scripts/cluster_labels`: largest-cluster fraction,
  tiebreak six-valent, then lowest T; needs scipy) → `yield_heroes.json`
  (84 sweep heroes, e.g. PHB3 bigSa1 T=0.16 at 1.000, PHB5/square/a1 T=0.075
  at 0.972).
- `prune_heroes.py` — enforces highest-yield-only: keeps `final.png` solely in
  each sweep's hero temperature dir (incl. deleting `main/` finals), prunes the
  rest (868 mass-rendered → 84 heroes). Helix/DNA systems (oxDNA `.top`, unreadable
  by render_phb/cluster_labels) use lowest-final-energy as the hero proxy, rendered
  via `cli/generate-image.js` against a local dev server.
- `render_ghost.py` / `run_ghost.sh` — clear2-style ghost compositing for the drive
  heroes (`render_phb.render_ghosted()`: tetrahedron-member molecules opaque, rest at
  12% opacity, ballstick, 1920x1080, text-free) → `final_ghost.png` next to each
  hero `final.png` (84/84; `clear2/render_clear2.py` itself needs `/scratch` data).
- `run_initials.sh` — `initial.png` in each hero dir from the sweep's starting
  configuration (`main/last_conf.dat`, or `main/100q.dat` for PHBcg/PHBformedLB/100
  which has no `last_conf.dat` there): ball model, species colors, text-free, 84/84.
  Both render scripts now pass `--species-colors` (hcc/hcc2 convention: core body by
  species, patches keep interaction colours); `species_key.json` maps every hero to
  its species→colour key (only 2 distinct mappings drive-wide: 4-species and 8-species).
