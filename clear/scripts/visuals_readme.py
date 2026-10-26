#!/usr/bin/env python3
"""Writes PHB_visuals_2026-10-23/README.md and index.json from the registry + metrics."""
import json, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_visuals as MV
OUT = str(MV.OUT)
M = {os.path.basename(f)[:-13]: json.load(open(f)) for f in glob.glob(OUT + "/images/*.metrics.json")}
V = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(OUT + "/videos/*.json")}
A = json.load(open(OUT + "/analysis/analysis.json"))
idx = []
for n, r in MV.REG.items():
    m = M[n]; topo = os.path.basename(os.path.dirname(r["top"])) + "__" + os.path.basename(r["top"])
    idx.append(dict(name=n, group=r["group"], label=r["label"], topology="topologies/" + topo, source_dir=r["dir"], initial_conf=f"confs/{n}_initial.dat", final_conf=f"confs/{n}_final.dat",
                    mgl=[f"mgl/{n}_{ph}_{k}.mgl" for ph in ("initial", "final") for k in ("species", "patches")], images=sorted(os.path.basename(p) for p in glob.glob(f"{OUT}/images/{n}_*")),
                    video=(f"videos/{n}.mp4" if n in V else None), turntable=(f"videos/{n}_turntable.mp4" if os.path.exists(f"{OUT}/videos/{n}_turntable.mp4") else None),
                    initial=m["initial"], final=m["final"]))
json.dump(idx, open(OUT + "/index.json", "w"), indent=1)
pc = lambda x: f"{100*x:.1f}%"
L = []
w = L.append
w("# PHB crystal-assembly visuals, 2026-10-23\n")
w("Snapshots, `.mgl` files for cogli, images and videos of the important PHB runs, plus a short write-up of where the analysis stands. Everything here was generated from the simulation directories under `large_crystal/hand5/` by `hand5/final_report/make_visuals.py` (renders), `render_species.py` (colour scheme), `make_videos.py` / `visuals_analysis.py` (frame indexing, figures) and the oxDNAcpp `terminal autoconvert` command (`.mgl` conversion).\n")
w("## 1. Folder layout\n")
w("| folder | content |\n|---|---|\n| `mgl/` | cogli `.mgl` files, **initial and final of every run**, two flavours each (see section 2) |\n| `images/` | PNG renders (1920x1080; crystal 2560x1440): `_iso` (whole box), `_close` (framed on the structure), `_slab{x,y,z}` (thin cut through the largest cluster, headline runs and the crystal), `_initial_vs_final.jpg`, and `<run>.metrics.json` |\n| `videos/` | `<run>.mp4`: 150 frames evenly spaced from the first to the last complete trajectory frame, 10 s, 1280x720, with the helix bundles drawn; `<run>_turntable.mp4`: the final state rotating; `<run>.json`: per-frame metrics |\n| `analysis/` | `ka_alpha.png`, `two_species_vs_T.png`, `timecourses_headline.png`, `analysis.json` |\n| `confs/`, `topologies/` | the exact initial/final `.dat` configurations and `.phb` topologies the files above were made from |\n| `index.json` | machine-readable list: run -> topology, configurations, files, metrics |\n| `*.slurm`, `logs/` | the Slurm scripts used (`-q private`) and their logs |\n")
w("## 2. The `.mgl` files (cogli)\n")
w("Open with `cogli2 mgl/<run>_final_species.mgl`. Positions are **wrapped molecule by molecule into the periodic box** (the raw trajectory coordinates of these runs are unwrapped and drift hundreds of units outside the box, which makes a raw conversion unreadable). Two flavours per snapshot:\n")
w("* `<run>_{initial,final}_patches.mgl` - made with oxDNAcpp's `terminal autoconvert` (colour per particle, patches drawn as small coloured spheres; patch colours follow the topology colour index, complementary pairs differ), with the positions replaced by the wrapped ones.\n* `<run>_{initial,final}_species.mgl` - no patches; one hue per **species**, arms lighter than cores, **six-valent cores darker**, molecules outside the **largest cluster washed out** (same scheme as the images and videos, below). Radii: cores 1.0, arm beads 0.1.\n")
w("## 3. Colour key (images, videos, `*_species.mgl`)\n")
w("* hue = species of the molecule: species I orange, II blue, III green, IV violet (2-species runs use only orange and blue);\n* the core is the large sphere, its three helix arms (five beads each) are drawn lighter so the bundle reads against the core;\n* **dark core = six-valent molecule** (bonded to six distinct neighbours: the crystal-like environment);\n* **washed grey-tinted = not in the largest cluster** (free molecules and small clusters), so a growing cluster stands out from what it has not yet captured;\n* bonds: complementary patch colours, patch distance < 0.3, minimum image (same detector as the written report).\n")
w("## 4. Runs\n")
w("`cl` = largest cluster, `6v` = six-valent molecules, `val` = mean valence (max 6), `tet` = intact four-molecule cliques per molecule (ideal crystal 0.358). 'initial' is the configuration the MD started from (after the short MC relaxation).\n")
w("| run | what | step (final) | cl | 6v | val | tet | initial cl / 6v |\n|---|---|---|---|---|---|---|---|")
cur = None
for r in idx:
    if r["group"] != cur:
        cur = r["group"]; w(f"| **{cur}** | | | | | | | |")
    f, i = r["final"], r["initial"]
    live = " (live)" if r["name"] in ("4sp_ws_T0.140",) else ""
    w(f"| `{r['name']}` | {r['label']}{live} | {f['step']:.3g} | {pc(f['largest_cluster'])} | {pc(f['six_valent'])} | {f['mean_valence']:.2f} | {f['tetra_per_molecule']:.3f} | {pc(i['largest_cluster'])} / {pc(i['six_valent'])} |")
w("")
open(OUT + "/README_tables.md", "w").write("\n".join(L))
print("tables", len(L))
