#!/usr/bin/env python3
"""Clean ball-and-stick renders with the assembled structure solid and everything else translucent.

A molecule counts as assembled when it belongs to at least one intact tetrahedron (a 4-clique of the
molecule bond graph, the crystal motif; bonds as in clear/scripts/cluster_labels.py). Assembled molecules are
drawn opaque, all other molecules at GHOST opacity. For every run of manifest.json it writes
clear2/<run>/<run>_{initial,final}_ballstick.png and a README.md.

  render_clear2.py list
  render_clear2.py run NAME [NAME..]
  render_clear2.py all [-j N]
"""
import argparse, datetime, json, os, sys, time
from multiprocessing import Pool
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent / "clear")); sys.path.insert(0, str(HERE.parent / "clear" / "scripts"))
import render_phb as RP
import cluster_labels as CL
import render_clear as RC

PHASES = ("initial", "final")
WIDTH, HEIGHT, SCALE = 3200, 2400, 2
GHOST = 0.12


def manifest():
    return {r["name"]: r for r in json.load(open(HERE / "manifest.json"))}


def tetra_members(nb):
    """Molecules that are part of at least one 4-clique; also the number of 4-cliques."""
    mem, n = set(), 0
    for a in nb:
        na = nb[a]
        for b in na:
            if b <= a:
                continue
            common = na & nb[b]
            for c in common:
                if c <= b:
                    continue
                for d in common & nb[c]:
                    if d > c:
                        n += 1
                        mem.update((a, b, c, d))
    return mem, n


def assembled(top, conf):
    topo = CL.load_topology(top)
    t, box, pos, a1, a3 = CL.load_conf(conf, topo["N"])
    res = CL.analyze_conf(topo, conf=(t, box, pos, a1, a3))
    mem, ntet = tetra_members(res["neighbors"])
    mol = np.asarray(topo["mol"])
    mask = np.isin(mol, np.fromiter(mem, int, len(mem))) if mem else np.zeros(len(mol), bool)
    return mask, len(mem), topo["n_mol"], ntet


def render_one(r, phase, out):
    mask, n_asm, n_mol, ntet = assembled(r["topology"], r[phase])
    args = RP.build_parser().parse_args(["--top", r["topology"], "--conf", r[phase], "--out", str(out),
                                         "--width", str(WIDTH), "--height", str(HEIGHT), "--scale", str(SCALE),
                                         "--model", "ballstick", "--background", "white", "--quiet"])
    args.title = None; args.legend = False; args.box = False
    args.solid = mask; args.ghost_opacity = GHOST
    RP.render(args, log=lambda *a: None)
    return n_asm, n_mol, ntet


def write_readme(r, outdir, stats, info):
    name = r["name"]
    (t0, box0), (t1, box1) = info["initial"], info["final"]
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(r["final"])).strftime("%Y-%m-%d %H:%M")
    src, kv, stages, meta = RC.read_params(r["dir"])
    L = [f"# {name}\n", f"**{r['label']}**  \nSeries: {r['group']}\n",
         "PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured "
         "interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA "
         "(`interaction_type = PHB`, CUDA, MD).\n", "## Images\n",
         f"Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, "
         f"legend, axes or box; white background; isometric orthographic view of the whole configuration; {WIDTH}x{HEIGHT} px.\n",
         "| file | configuration |\n|---|---|",
         f"| `{name}_initial_ballstick.png` | starting configuration |",
         f"| `{name}_final_ballstick.png` | last configuration |",
         f"\n**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron "
         f"(four mutually bonded molecules, the crystal motif); every other molecule is drawn at {int(GHOST * 100)}% opacity. "
         "Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in "
         "`clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.\n",
         "| | step | molecules in tetrahedra (opaque) | intact tetrahedra |\n|---|---|---|---|"]
    for nm, t, s in (("start", t0, stats["initial"]), ("last", t1, stats["final"])):
        L.append(f"| {nm} | {t:.4g} | {s[0]} of {s[1]} ({100 * s[0] / s[1]:.1f}%) | {s[2]} |")
    L += ["\n## Simulation\n", f"* run directory: `{r['dir']}`\n* topology: `{r['topology']}`",
          f"* molecules: {stats['final'][1]}; box {box1[0]:g} x {box1[1]:g} x {box1[2]:g}"]
    if kv:
        L.append(f"* parameters (from `{src}`): " + ", ".join(f"{k} = {v}" for k, v in kv.items()))
    if stages:
        L.append("* staged protocol (`stages.txt`: temperature, steps): " + "; ".join(f"T={a} x {int(float(b)):,}" for a, b in stages))
    L.append(f"* starting configuration: `{r['initial']}` (step {t0:.4g})")
    L.append(f"* last configuration: `{r['final']}` (step {t1:.4g}, file last written {mt}; the run may have continued since)\n")
    L.append("## Regenerate\n\n```\npython clear2/render_clear2.py run " + name + "\n```\n")
    (outdir / "README.md").write_text("\n".join(L))


def do_run(name):
    r = manifest()[name]
    outdir = HERE / name; outdir.mkdir(exist_ok=True)
    t_start = time.time(); stats, info = {}, {}
    for ph in PHASES:
        info[ph] = RC.conf_info(r[ph])
        stats[ph] = render_one(r, ph, outdir / f"{name}_{ph}_ballstick.png")
    write_readme(r, outdir, stats, info)
    return name, round(time.time() - t_start, 1), stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "run", "all"]); ap.add_argument("names", nargs="*")
    ap.add_argument("-j", type=int, default=4)
    a = ap.parse_args(); M = manifest()
    if a.cmd == "list":
        print("\n".join(M)); return
    names = a.names if a.cmd == "run" else list(M)
    with Pool(a.j) as p:
        for n, s, st in p.imap_unordered(do_run, names):
            print(f"done {n} in {s}s  assembled start {st['initial'][0]}/{st['initial'][1]} last {st['final'][0]}/{st['final'][1]}", flush=True)


if __name__ == "__main__":
    main()
