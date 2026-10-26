#!/usr/bin/env python3
"""Trajectory -> MP4 for the important PHB runs (ppview render_phb.py frames, PBC-safe cluster colouring).

  make_videos.py --list
  make_videos.py NAME [--frames 150] [--fps 15] [--procs 8] [--width 1280 --height 720] [--out DIR]

Every video: frames sampled evenly from the FIRST to the LAST COMPLETE frame (a frame cut off by a live run is dropped),
cores only, fixed camera (box fitted), caption = step | largest cluster | six-valent | mean valence.
mode 'val6'    : red = molecule bonded to 6 neighbours, grey = rest (gels: everything is one cluster).
mode 'cluster' : largest cluster coloured, other clusters/singletons faded (seeded growth).
Also writes <name>.json (frame steps, metrics, completeness flags) next to the mp4.
"""
import argparse, json, mmap, os, shutil, subprocess, sys, tempfile, time
from multiprocessing import Pool
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cluster_labels as CL  # noqa: E402

R = HERE.parent
PP = "/scratch/sroy85/Github/ppview/render_phb.py"
OUT = Path("/scratch/sroy85/Github/dna/large_crystal/videos/v2")
FF = None

REG = {}
def add(name, rundir, mode, title, top=None):
    REG[name] = dict(name=name, dir=str(R / rundir), top=top or str(R / rundir / "topology.phb"), traj=str(R / rundir / "trajectory.dat"), mode=mode, title=name.split("_",1)[1] if "_" in name else name)

for v in ("equal", "3H3L", "5H1L", "5L1H"):
    for T in ("0.140", "0.078"):
        if T == "0.078" and v in ("equal", "5H1L"): continue
        add(f"twospec_{v}_T{T}", f"two_species_preconnected/{v}/Kb_300_T_{T}", "val6", f"2-species {v} T={T}")
for s in ("weak_weak", "weak_strong"):
    for T in ("0.140", "0.078"):
        if s == "weak_strong" and T == "0.078": continue
        add(f"fourspec_{s}_T{T}", f"preconnected_K300_large/{s}/Kb_300_T_{T}", "val6", f"4-species {s} T={T}")
for T in ("0.140", "0.200"):
    add(f"fourspec_seed8_T{T}", f"preconnected_seed_sweep/four_species/Kb_300_T_{T}", "cluster", f"4-species 8-seed ws T={T}")
add("seeded_ww_Kb300_T0.078", "seeded_sweep/weak_weak/Kb_300_T_0.078", "cluster", "dilute 8-seed ww K=2 Kb=300 T=0.078")
for rn, T, ttl in (("Q_T0.140_a", "0.14", "melt-quench hold"), ("H_a", "", "heating ramp"), ("AS_a", "", "slow anneal")):
    add(f"window_{rn}", f"window_scan/runs/{rn}", "val6", f"window scan {ttl} {rn}")
for rn in ("S8_T0.140", "S8_T0.160", "S32_T0.150", "S64_T0.140", "S128_T0.140_r2", "S128_T0.150", "S128_T0.160", "S192_T0.140_r1", "S256_T0.140_r1"):
    add(f"seeding_{rn}", f"seeding_scan/runs/{rn}", "cluster", f"seeding scan {rn} (4-species ww K=2)")
for v in ("3H3L", "5L1H"):
    for T in ("0.150", "0.160", "0.170", "0.180"):
        add(f"highT_TS_{v}_T{T}", f"seeding_scan/runs/TS_{v}_T{T}", "val6", f"2-species {v} high-T T={T}")
for ka in ("10", "30", "100", "1000"):
    for a in ("0.10", "0.12"):
        add(f"Ka_S128_Ka{ka}_a{a}", f"seeding_scan/runs/KA_S128_T0.140_Ka{ka}_a{a}", "cluster", f"Ka={ka} alpha={a} S128 T=0.14")
add("Ka_S128_Ka300_a0.12", "seeding_scan/runs/KA_S128_T0.140_Ka300_a0.12", "cluster", "Ka=300 alpha=0.12 S128 T=0.14")


def frame_index(path):
    """[(start, end)] of every COMPLETE frame (byte offsets) via mmap; N from the first frame."""
    with open(path, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        size = len(mm)
        starts = [0]
        first = mm.find(b"\nt = ", 5)
        avg = first + 1 if first > 0 else size
        p = 0
        while True:
            q = mm.find(b"\nt = ", max(p + int(avg * 0.9), p + 1))
            if q < 0: break
            starts.append(q + 1); p = q + 1
        ends = starts[1:] + [size]
        mm.close()
    # a frame is complete if it is within 0.5% of the median size (last one may be truncated while the run is live)
    sizes = np.array([e - s for s, e in zip(starts, ends)])
    med = np.median(sizes)
    ok = [(s, e) for (s, e), z in zip(zip(starts, ends), sizes) if abs(z - med) <= 0.005 * med + 200]
    return ok, len(starts), int(med)


def work(a):
    k, text, top, mode, title, width, height, tmp = a
    topo = WORK["topo"]
    t, box, pos, a1, a3 = CL.parse_frame_text(text)
    res = CL.analyze_conf(topo, conf=(t, box, pos, a1, a3))
    n = topo["n_mol"]; val = res["valence"]
    lab_mol = res["mol_label"]
    big = int((lab_mol == 0).sum()); v6 = float((val == 6).mean())
    if mode == "val6":
        lab = np.where(val == 6, 0, -1)
    else:
        lab = lab_mol.copy(); lab[lab_mol > 0] = -1  # largest cluster only
    labp = lab[topo["mol"]]
    conf = f"{tmp}/c{k:05d}.dat"; lf = f"{tmp}/l{k:05d}.txt"; png = f"{tmp}/f{k:05d}.png"
    open(conf, "w").write(text); np.savetxt(lf, labp, fmt="%d")
    cap = f"{title} | step {t:.2e} | cluster {100*big/n:.0f}% | 6-valent {100*v6:.1f}% | val {val.mean():.2f}"
    subprocess.run([sys.executable, PP, "--top", top, "--conf", conf, "--out", png, "--width", str(width), "--height", str(height),
                    "--scale", "1", "--background", "white", "--cluster-file", lf, "--min-cluster-mols", "1", "--cores-only",
                    "--fit", "box", "--title", cap, "--quiet"], check=True, stdout=subprocess.DEVNULL)
    os.remove(conf); os.remove(lf)
    return dict(k=k, step=t, largest=big / n, six=v6, valence=float(val.mean()), png=png)

WORK = {}
def init(top):
    WORK["topo"] = CL.load_topology(top)


def main():
    global FF
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?"); ap.add_argument("--list", action="store_true")
    ap.add_argument("--frames", type=int, default=150); ap.add_argument("--fps", type=int, default=15)
    ap.add_argument("--procs", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", 4)))
    ap.add_argument("--width", type=int, default=1280); ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    if a.list:
        for i, n in enumerate(REG): print(i, n)
        return
    r = REG[a.name] if a.name in REG else REG[list(REG)[int(a.name)]]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    idx, nraw, med = frame_index(r["traj"])
    N = CL.load_topology(r["top"])["N"]
    print(f"{r['name']}: {len(idx)} complete frames of {nraw} headers (median {med/1e6:.2f} MB); {time.time()-t0:.0f}s", flush=True)
    sel = np.unique(np.linspace(0, len(idx) - 1, min(a.frames, len(idx))).round().astype(int))
    mm = open(r["traj"], "rb")
    texts = []
    for i in sel:
        s, e = idx[i]; mm.seek(s); texts.append(mm.read(e - s).decode())
    mm.close()
    tmp = tempfile.mkdtemp(prefix="vid_", dir=os.environ.get("TMPDIR", "/tmp"))
    tasks = [(j, tx, r["top"], r["mode"], r["title"], a.width, a.height, tmp) for j, tx in enumerate(texts)]
    with Pool(a.procs, initializer=init, initargs=(r["top"],)) as pool:
        rows = pool.map(work, tasks, chunksize=1)
    ff = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    mp4 = out / f"{r['name']}.mp4"
    subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", f"{tmp}/f%05d.png", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", str(mp4)], check=True)
    steps = [x["step"] for x in rows]
    meta = dict(name=r["name"], trajectory=r["traj"], mode=r["mode"], frames_in_video=len(rows), complete_frames_in_file=len(idx), headers_in_file=nraw,
                dropped_incomplete_frames=nraw - len(idx), first_step=steps[0], last_step=steps[-1], monotonic_steps=bool(np.all(np.diff(steps) >= 0)),
                final_largest_cluster=rows[-1]["largest"], final_six_valent=rows[-1]["six"], final_valence=rows[-1]["valence"],
                per_frame=[{k: x[k] for k in ("step", "largest", "six", "valence")} for x in rows], seconds=round(time.time() - t0))
    json.dump(meta, open(out / f"{r['name']}.json", "w"))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"WROTE {mp4} ({mp4.stat().st_size/1e6:.1f} MB) steps {steps[0]:.3g}..{steps[-1]:.3g} monotonic={meta['monotonic_steps']} in {meta['seconds']}s", flush=True)

if __name__ == "__main__":
    main()
