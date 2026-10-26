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
- The `plot.sh` files in `gnuplot/` also show the per-frame variant:
  `terminal autoconvert -i <topology> -d last_conf.dat -o last.mgl`.

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
