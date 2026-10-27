#!/usr/bin/env python3
"""Clean (no text, no legend, no box) renders of the PHB runs for figures.

For every run of manifest.json it writes  hcc/<run>/<run>_{initial,final}_{ball,ballstick}.png  and a README.md
describing the run. Models: `ball` is the ppview PHB model (cores and arm beads as spheres, patches coloured by
interaction colour); `ballstick` draws cores as balls and each helix arm as small joint balls joined by sticks.

  render_clear.py list
  render_clear.py run NAME [NAME..]      render + README for these runs
  render_clear.py all [-j N]             every run in the manifest
"""
import argparse, datetime, json, os, re, sys, time
from multiprocessing import Pool
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent / "clear" / "scripts"))
import render_phb as RP
import cluster_labels as CL

MODELS = ("ball", "ballstick")
PHASES = ("initial", "final")
WIDTH, HEIGHT, SCALE = 3200, 2400, 2
PARAM_KEYS = ("T", "dt", "steps", "thermostat", "Ka", "Kb", "patchyAlpha", "rcut", "backend", "interaction_type", "seed")


def manifest():
    return {r["name"]: r for r in json.load(open(HERE / "manifest.json"))}


def render_one(r, phase, model, out):
    args = RP.build_parser().parse_args(["--top", r["topology"], "--conf", r[phase], "--out", str(out),
                                         "--width", str(WIDTH), "--height", str(HEIGHT), "--scale", str(SCALE),
                                         "--model", model, "--background", "white", "--species-colors", "--quiet"])
    # no title, no legend, no periodic box: argparse defaults, restated so a future default change cannot add text
    args.title = None; args.legend = False; args.box = False
    RP.render(args, log=lambda *a: None)


def conf_info(path):
    with open(path) as f:
        t = f.readline().split("=")[1].split()[0]
        box = f.readline().split("=")[1].split()
    return float(t), [float(x) for x in box]


def metrics(top, conf):
    topo = CL.load_topology(top)
    t, box, pos, a1, a3 = CL.load_conf(conf, topo["N"])
    res = CL.analyze_conf(topo, conf=(t, box, pos, a1, a3))
    n = topo["n_mol"]; val = res["valence"]
    cl = CL.clique_stats(topo, res["neighbors"]) if n < 3000 else {}
    return dict(n_molecules=int(n), largest_cluster=float((res["mol_label"] == 0).sum() / n),
                n_clusters=int(res["mol_label"].max() + 1), mean_valence=float(val.mean()),
                six_valent=float((val == 6).mean()),
                tetra=float(cl.get("n_tetra", 0) / n) if cl else None)


def read_params(d):
    d = Path(d)
    f = next((d / n for n in ("input", "input_stage", "input_md_production") if (d / n).exists()), None)
    kv, src = {}, None
    if f is not None:
        src = f.name
        for line in open(f):
            m = re.match(r"\s*([A-Za-z_]+)\s*=\s*(\S+)", line)
            if m and m.group(1) in PARAM_KEYS:
                kv[m.group(1)] = m.group(2)
    stages = (d / "stages.txt").read_text().split("\n") if (d / "stages.txt").exists() else []
    stages = [s.split() for s in stages if s.strip()]
    meta = json.load(open(d / "meta.json")) if (d / "meta.json").exists() else None
    return src, kv, stages, meta


def fmt_steps(x):
    return f"{x:.4g}"


def write_readme(r, outdir, info):
    src, kv, stages, meta = read_params(r["dir"])
    (t0, box0), (t1, box1) = info["initial"], info["final"]
    m0, m1 = info["metrics"]["initial"], info["metrics"]["final"]
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(r["final"])).strftime("%Y-%m-%d %H:%M")
    L = []
    L.append(f"# {r['name']}\n")
    L.append(f"**{r['label']}**  \nSeries: {r['group']}\n")
    L.append("PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured "
             "interaction patches) carrying three helix arms of five beads (radius 0.1). Arms bind cores "
             "through complementary patches (colours c and -c). Simulated with oxDNA (`interaction_type = PHB`, "
             "CUDA, MD).\n")
    L.append("## Images\n")
    L.append("Pure configuration renders: no title, legend, axes or periodic box; white background; isometric "
             f"orthographic view of the whole configuration; {WIDTH}x{HEIGHT} px.\n")
    L.append("| file | configuration | model |\n|---|---|---|")
    for ph in PHASES:
        for mo in MODELS:
            what = "starting configuration" if ph == "initial" else "last configuration"
            how = ("ppview ball model: cores and arm beads as spheres" if mo == "ball"
                   else "ball-and-stick: core balls, arm joint balls joined by sticks")
            L.append(f"| `{r['name']}_{ph}_{mo}.png` | {what} | {how} |")
    tp = RP.parse_topology(r["topology"]); sp_types, sp_cmap = RP.species_colors(tp.ptype, tp.btype)
    L.append("\nCore body colour = species (core bead type): " + ", ".join(f"species {i} ({t}) = {sp_cmap[t]}" for i, t in enumerate(sp_types)) + ".")
    L.append("Colours: arm beads/sticks are slate; each patch on a core is coloured by its "
             "interaction colour id, and a complementary pair (c, -c) shares one colour, so two bonded cores "
             "show a matching coloured patch where they touch. Hue is keyed on |c| mod 500; the darker variant "
             "marks |c| >= 500 (the strong channels).\n")
    L.append("## Simulation\n")
    L.append(f"* run directory: `{r['dir']}`\n* topology: `{r['topology']}`")
    L.append(f"* molecules: {m1['n_molecules']}; box {box1[0]:g} x {box1[1]:g} x {box1[2]:g}")
    if kv:
        L.append(f"* parameters (from `{src}`): " + ", ".join(f"{k} = {v}" for k, v in kv.items()))
    if stages:
        L.append("* staged protocol (`stages.txt`: temperature, steps): " + "; ".join(f"T={a} x {int(float(b)):,}" for a, b in stages))
    if meta:
        L.append(f"* run metadata (`meta.json`): `{json.dumps(meta)[:600]}`")
    L.append(f"* starting configuration: `{r['initial']}` (step {fmt_steps(t0)}; the configuration the MD started from, after the short MC relaxation where one was run)")
    L.append(f"* last configuration: `{r['final']}` (step {fmt_steps(t1)}, file last written {mt}; the run may have continued since)\n")
    L.append("## Structure at the two configurations\n")
    L.append("Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), "
             "as in `clear/scripts/cluster_labels.py`.\n")
    L.append("| | step | largest cluster | clusters | mean valence (max 6) | six-valent molecules | intact tetrahedra per molecule |\n|---|---|---|---|---|---|---|")
    for nm, t, m in (("start", t0, m0), ("last", t1, m1)):
        tet = "n/a" if m["tetra"] is None else f"{m['tetra']:.3f}"
        L.append(f"| {nm} | {fmt_steps(t)} | {100 * m['largest_cluster']:.1f}% | {m['n_clusters']} | {m['mean_valence']:.2f} | {100 * m['six_valent']:.1f}% | {tet} |")
    L.append("\n(ideal crystal: 0.358 tetrahedra per molecule, six-valent 100%)\n")
    L.append("## Regenerate\n")
    L.append("```\npython hcc/render_clear.py run " + r["name"] + "\n```\n"
             "or directly: `python render_phb.py --top <topology> --conf <conf> --out img.png --width "
             f"{WIDTH} --height {HEIGHT} --model ball|ballstick`.\n")
    (outdir / "README.md").write_text("\n".join(L))


def do_run(name):
    r = manifest()[name]
    outdir = HERE / name; outdir.mkdir(exist_ok=True)
    t_start = time.time()
    info = dict(metrics={})
    for ph in PHASES:
        info[ph] = conf_info(r[ph])
        info["metrics"][ph] = metrics(r["topology"], r[ph])
        for mo in MODELS:
            render_one(r, ph, mo, outdir / f"{name}_{ph}_{mo}.png")
    write_readme(r, outdir, info)
    return name, round(time.time() - t_start, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "run", "all"]); ap.add_argument("names", nargs="*")
    ap.add_argument("-j", type=int, default=4)
    a = ap.parse_args()
    M = manifest()
    if a.cmd == "list":
        print("\n".join(M)); return
    names = a.names if a.cmd == "run" else list(M)
    with Pool(a.j) as p:
        for n, s in p.imap_unordered(do_run, names):
            print(f"done {n} in {s}s", flush=True)


if __name__ == "__main__":
    main()
