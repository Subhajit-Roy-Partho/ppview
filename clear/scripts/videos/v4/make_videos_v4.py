#!/usr/bin/env python3
"""Trajectory -> MP4 v3: complete first..last frames, species colouring, crystal end-highlight.

New file (does not modify make_videos.py; imports its REG + frame_index read-only).

  make_videos_v3.py --list
  make_videos_v4.py NAME [--color-mode species_cluster] [--frames 150] [--fps 8]
                   [--procs 8] [--width 1280 --height 720] [--out DIR]
                   [--end-hold 30 | --no-end-hold]

v4 changes vs v3: (1) default fps 8 (slower); (2) species_cluster mode paints
molecules OUTSIDE the largest cluster solid grey (#9aa0a8) instead of faded
species colours, so attached vs unattached is obvious while species stay
distinct inside the cluster.

Colour modes (body of the video):
  species          : every molecule coloured by species (A/B or A-D), consistent palette
  species_cluster  : (default) species colours for molecules IN the largest cluster,
                     solid grey for molecules outside it (attached vs unattached
                     is obvious; project-wide species legend, comparable studies)
  cluster          : legacy: largest cluster saturated, rest faded
  val6             : legacy: red = valence-6 molecule, grey = rest

End highlight: the LAST frame is additionally rendered with crystal-membership
colours (bulk=#d00000, surface=#ff9e00, liquid=#9aa0a8; see crystal_label.py)
and held for --end-hold frames (~2 s), captioned as END highlight, so every
video ends with the crystal visibly highlighted.

Writes <name>.mp4 + <name>.json (frame steps, completeness flags, colour mode,
crystal counts, trajectory last-step at render time).
"""
import argparse
import json
import mmap
import os
import shutil
import subprocess
import sys
import tempfile
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "hand5" / "final_report"))
import cluster_labels as CL  # noqa: E402
import make_videos as MV  # noqa: E402  (REG + frame_index, read-only)
import species_colors as SC  # noqa: E402

REG = MV.REG
PP = str(HERE / "render_phb_v3.py")
OUT = HERE
FF = None

CLUSTER_PALETTE = ["#e4572e", "#2e86de", "#2fb344", "#f2a900", "#8e44ad", "#17bebb",
                   "#d6336c", "#7f8c2a", "#0b5ea8", "#c0762d", "#5f3dc4", "#12a07a",
                   "#e0457b", "#4c6ef5", "#99a31f", "#a23e48"]
UNASSIGNED = "#8a8f98"


def cluster_hex(rank):
    if rank < len(CLUSTER_PALETTE):
        return CLUSTER_PALETTE[rank]
    h = (rank * 137.508) % 360
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h / 360.0, 0.55, 0.6)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def work(a):
    (k, text, top, mode, cmode, title, width, height, tmp,
     end_hold, total_body, crystal_rgb, crystal_leg) = a
    topo = WORK["topo"]
    t, box, pos, a1, a3 = CL.parse_frame_text(text)
    res = CL.analyze_conf(topo, conf=(t, box, pos, a1, a3))
    n = topo["n_mol"]
    val = res["valence"]
    lab_mol = res["mol_label"]
    big = int((lab_mol == 0).sum())
    v6 = float((val == 6).mean())
    species = topo["species"]  # per molecule
    is_end_hold = k >= total_body
    conf = f"{tmp}/c{k:05d}.dat"
    png = f"{tmp}/f{k:05d}.png"
    open(conf, "w").write(text)
    if is_end_hold:
        # crystal end-highlight frames: bulk red / surface orange / liquid grey
        open(f"{tmp}/rgb{k:05d}.txt", "w").write("\n".join(crystal_rgb) + "\n")
        open(f"{tmp}/leg{k:05d}.json", "w").write(json.dumps(crystal_leg))
        cap = (f"{title} | step {t:.2e} | END crystal: bulk {WORK['n_bulk']} "
               f"surface {WORK['n_surf']} liquid {WORK['n_liq']} mol")
        cmd = [sys.executable, PP, "--top", top, "--conf", conf, "--out", png,
               "--width", str(width), "--height", str(height),
               "--scale", "1", "--background", "white",
               "--rgb-file", f"{tmp}/rgb{k:05d}.txt",
               "--legend-json", f"{tmp}/leg{k:05d}.json",
               "--legend", "--cores-only", "--fit", "box",
               "--title", cap, "--quiet"]
    elif cmode in ("species", "species_cluster"):
        if cmode == "species_cluster":
            # v4: in-cluster = species colours, outside largest cluster = solid grey
            in_cl = (lab_mol == 0)
            n_out = int((~in_cl).sum())
            grey = SC.CRYSTAL_PALETTE["liquid"]
            rgb_mol = [SC.SPECIES_PALETTE[int(s)] if in_cl[m] else grey
                       for m, s in enumerate(species)]
            rgb = [rgb_mol[m] for m in topo["mol"]]
            open(f"{tmp}/rgb{k:05d}.txt", "w").write("\n".join(rgb) + "\n")
            leg = {"title": f"Species in cluster ({n - n_out}/{n} mol attached, grey = outside)",
                   "entries": [[SC.SPECIES_PALETTE[s], f"species {SC.species_names(len(set(species.tolist())))[s]} in cluster (btype {s})"]
                               for s in sorted(set(species.tolist()))] + [[grey, f"outside largest cluster: {n_out} mol"]],
                   "footer": None}
            open(f"{tmp}/leg{k:05d}.json", "w").write(json.dumps(leg))
            cmd = [sys.executable, PP, "--top", top, "--conf", conf, "--out", png,
                   "--width", str(width), "--height", str(height),
                   "--scale", "1", "--background", "white",
                   "--rgb-file", f"{tmp}/rgb{k:05d}.txt",
                   "--legend-json", f"{tmp}/leg{k:05d}.json",
                   "--legend", "--cores-only", "--fit", "box"]
            cap = (f"{title} | step {t:.2e} | cluster {100*big/n:.0f}% "
                   f"| 6-valent {100*v6:.1f}% | val {val.mean():.2f}")
        else:
            rgb_mol = [SC.SPECIES_PALETTE[int(s)] for s in species]
            rgb = [rgb_mol[m] for m in topo["mol"]]
            open(f"{tmp}/rgb{k:05d}.txt", "w").write("\n".join(rgb) + "\n")
            leg = {"title": f"Species ({len(set(species.tolist()))} types, {n} mol)",
                   "entries": [[SC.SPECIES_PALETTE[s], f"species {SC.species_names(len(set(species.tolist())))[s]} (btype {s}): {int((species == s).sum())} mol"]
                               for s in sorted(set(species.tolist()))],
                   "footer": None}
            open(f"{tmp}/leg{k:05d}.json", "w").write(json.dumps(leg))
            cmd = [sys.executable, PP, "--top", top, "--conf", conf, "--out", png,
                   "--width", str(width), "--height", str(height),
                   "--scale", "1", "--background", "white",
                   "--rgb-file", f"{tmp}/rgb{k:05d}.txt",
                   "--legend-json", f"{tmp}/leg{k:05d}.json",
                   "--legend", "--cores-only", "--fit", "box"]
            cap = (f"{title} | step {t:.2e} | cluster {100*big/n:.0f}% "
                   f"| 6-valent {100*v6:.1f}% | val {val.mean():.2f}")
        cmd += ["--title", cap, "--quiet"]
    elif mode == "val6" and cmode in ("cluster", "val6"):
        lab = np.where(val == 6, 0, -1)
        labp = lab[topo["mol"]]
        lf = f"{tmp}/l{k:05d}.txt"
        np.savetxt(lf, labp, fmt="%d")
        cap = (f"{title} | step {t:.2e} | cluster {100*big/n:.0f}% "
               f"| 6-valent {100*v6:.1f}% | val {val.mean():.2f}")
        cmd = [sys.executable, PP, "--top", top, "--conf", conf, "--out", png,
               "--width", str(width), "--height", str(height),
               "--scale", "1", "--background", "white",
               "--cluster-file", lf, "--min-cluster-mols", "1",
               "--cores-only", "--fit", "box", "--title", cap, "--quiet"]
    else:
        lab = lab_mol.copy()
        lab[lab_mol > 0] = -1
        labp = lab[topo["mol"]]
        lf = f"{tmp}/l{k:05d}.txt"
        np.savetxt(lf, labp, fmt="%d")
        cap = (f"{title} | step {t:.2e} | cluster {100*big/n:.0f}% "
               f"| 6-valent {100*v6:.1f}% | val {val.mean():.2f}")
        cmd = [sys.executable, PP, "--top", top, "--conf", conf, "--out", png,
               "--width", str(width), "--height", str(height),
               "--scale", "1", "--background", "white",
               "--cluster-file", lf, "--min-cluster-mols", "1", "--cores-only",
               "--fit", "box", "--title", cap, "--quiet"]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    for f in (conf, f"{tmp}/rgb{k:05d}.txt", f"{tmp}/leg{k:05d}.json",
              f"{tmp}/fade{k:05d}.txt", f"{tmp}/l{k:05d}.txt"):
        try:
            os.remove(f)
        except OSError:
            pass
    return dict(k=k, step=t, largest=big / n, six=v6, valence=float(val.mean()), png=png)


WORK = {}


def init(top):
    WORK["topo"] = CL.load_topology(top)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--color-mode", default="species_cluster",
                    choices=["species", "species_cluster", "cluster", "val6"])
    ap.add_argument("--frames", type=int, default=150)
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--procs", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", 4)))
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--end-hold", type=int, default=30)
    ap.add_argument("--no-end-hold", action="store_true")
    a = ap.parse_args()
    if a.list:
        for i, n in enumerate(REG):
            print(i, n)
        return
    r = REG[a.name] if a.name in REG else REG[list(REG)[int(a.name)]]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    idx, nraw, med = MV.frame_index(r["traj"])
    N = CL.load_topology(r["top"])["N"]
    print(f"{r['name']}: {len(idx)} complete frames of {nraw} headers "
          f"(median {med/1e6:.2f} MB); {time.time()-t0:.0f}s", flush=True)
    nbody = min(a.frames, len(idx))
    sel = np.unique(np.linspace(0, len(idx) - 1, nbody).round().astype(int))
    mm = open(r["traj"], "rb")
    texts = []
    for i in sel:
        s, e = idx[i]
        mm.seek(s)
        texts.append(mm.read(e - s).decode())
    mm.close()
    # completeness flags: first/last sampled frame must be first/last complete frame
    first_ok = bool(sel[0] == 0)
    last_ok = bool(sel[-1] == len(idx) - 1)
    # crystal classes of the final frame (end highlight + json numbers)
    topo0 = CL.load_topology(r["top"])
    res0 = CL.analyze_conf(topo0, conf=CL.parse_frame_text(texts[-1]))
    n_mol = topo0["n_mol"]
    in_largest = res0["mol_label"] == 0
    val0 = res0["valence"]
    cls_mol = np.where(in_largest, np.where(val0 == 6, "bulk", "surface"), "liquid")
    n_bulk, n_surf = int((cls_mol == "bulk").sum()), int((cls_mol == "surface").sum())
    n_liq = int((cls_mol == "liquid").sum())
    cmap = {"bulk": SC.CRYSTAL_PALETTE["bulk"], "surface": SC.CRYSTAL_PALETTE["surface"],
            "liquid": SC.CRYSTAL_PALETTE["liquid"]}
    crystal_rgb = [cmap[cls_mol[m]] for m in topo0["mol"]]
    crystal_leg = {"title": f"END crystal ({100*(n_bulk+n_surf)/n_mol:.0f}% of {n_mol} mol)",
                   "entries": [[cmap["bulk"], f"bulk crystal (val 6): {n_bulk} mol"],
                               [cmap["surface"], f"surface (largest cl, val<6): {n_surf} mol"],
                               [cmap["liquid"], f"liquid/gel: {n_liq} mol"]],
                   "footer": None}
    WORK_hold = a.end_hold if not a.no_end_hold else 0
    tmp = tempfile.mkdtemp(prefix="vid3_", dir=os.environ.get("TMPDIR", "/tmp"))
    WORK.update(n_bulk=n_bulk, n_surf=n_surf, n_liq=n_liq)
    tasks = [(j, tx, r["top"], r["mode"], a.color_mode, r["title"], a.width, a.height,
              tmp, WORK_hold, len(texts), crystal_rgb, crystal_leg)
             for j, tx in enumerate(texts)]
    if WORK_hold:
        tasks += [(len(texts) + h, texts[-1], r["top"], r["mode"], a.color_mode,
                   r["title"], a.width, a.height, tmp, WORK_hold, len(texts),
                   crystal_rgb, crystal_leg) for h in range(WORK_hold)]
    with Pool(a.procs, initializer=init, initargs=(r["top"],)) as pool:
        rows = pool.map(work, tasks, chunksize=1)
    rows.sort(key=lambda x: x["k"])
    # rename held frames sequentially (already sequential k) -> f%05d
    ff = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    mp4 = out / f"{r['name']}.mp4"
    subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(a.fps),
                    "-i", f"{tmp}/f%05d.png", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "22", str(mp4)], check=True)
    steps = [x["step"] for x in rows]
    body = rows[:len(texts)]
    meta = dict(name=r["name"], trajectory=r["traj"], mode=r["mode"], color_mode=a.color_mode,
                frames_in_video=len(rows), body_frames=len(texts), end_hold_frames=WORK_hold,
                complete_frames_in_file=len(idx), headers_in_file=nraw,
                dropped_incomplete_frames=nraw - len(idx),
                first_step=steps[0], last_step=steps[len(texts) - 1],
                first_is_first_complete=first_ok, last_is_last_complete=last_ok,
                uniform_sampling=True,
                monotonic_steps=bool(np.all(np.diff(np.array(steps[:len(texts)])) >= 0)),
                final_largest_cluster=body[-1]["largest"], final_six_valent=body[-1]["six"],
                final_valence=body[-1]["valence"],
                end_bulk_mol=n_bulk, end_surface_mol=n_surf, end_liquid_mol=n_liq,
                end_frac_crystal=(n_bulk + n_surf) / n_mol,
                per_frame=[{k: x[k] for k in ("step", "largest", "six", "valence")} for x in body],
                seconds=round(time.time() - t0))
    json.dump(meta, open(out / f"{r['name']}.json", "w"))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"WROTE {mp4} ({mp4.stat().st_size/1e6:.1f} MB) steps {steps[0]:.3g}..{steps[len(texts)-1]:.3g} "
          f"first_ok={first_ok} last_ok={last_ok} monotonic={meta['monotonic_steps']} "
          f"in {meta['seconds']}s", flush=True)


if __name__ == "__main__":
    main()
