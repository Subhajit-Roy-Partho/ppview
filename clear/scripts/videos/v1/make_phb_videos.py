#!/usr/bin/env python3
"""Render PHB oxDNA trajectories to MP4 with frameskip.

Usage: python3 make_phb_videos.py
Produces videos/*.mp4. Streams trajectories (never loads full file),
samples ~TARGET_FRAMES evenly via frameskip, wraps positions into box.
ICO cores (type -3 from topology) plotted large/gold; beads small/blue.
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio_ffmpeg

VIDDIR = "/scratch/sroy85/Github/dna/large_crystal/videos"
TMPBASE = "/tmp/opencode/phb_frames"
TARGET_FRAMES = 150
FPS = 12

RUNS = "/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs"
TWOSPEC = "/scratch/sroy85/Github/dna/large_crystal/hand5/two_species_preconnected"

JOBS_BATCH2 = [
    dict(name="seed_TS_3H3L_T0.170",
         traj=f"{RUNS}/TS_3H3L_T0.170/trajectory.dat",
         top=f"{RUNS}/TS_3H3L_T0.170/topology.phb",
         title="Seeded 2-species 3H3L T=0.170 STRONG GROWTH (PE -37.2 -> -49.1, ICO gold + beads blue)",
         ico_only=False),
    dict(name="seed_TS_3H3L_T0.150",
         traj=f"{RUNS}/TS_3H3L_T0.150/trajectory.dat",
         top=f"{RUNS}/TS_3H3L_T0.150/topology.phb",
         title="Seeded 2-species 3H3L T=0.150 growth at lower T (PE -37.3 -> -48.4)",
         ico_only=False),
    dict(name="seed_TS_5L1H_T0.170",
         traj=f"{RUNS}/TS_5L1H_T0.170/trajectory.dat",
         top=f"{RUNS}/TS_5L1H_T0.170/topology.phb",
         title="Seeded 2-species 5L1H T=0.170 WEAK growth contrast (PE -37.2 -> -41.5)",
         ico_only=False),
    dict(name="seed_S128_T0.140",
         traj=f"{RUNS}/S128_T0.140/trajectory.dat",
         top=f"{RUNS}/S128_T0.140/topology.phb",
         title="Seed-size scan S128 T=0.140: big seed INTACT but static, no growth (PE ~ -18.8 flat)",
         ico_only=False),
    dict(name="seed_S8_T0.160",
         traj=f"{RUNS}/S8_T0.160/trajectory.dat",
         top=f"{RUNS}/S8_T0.160/topology.phb",
         title="Seed-size scan S8 T=0.160: small seed MELTS (PE rises -18.62 -> -18.64)",
         ico_only=False),
    dict(name="seed_S128_T0.160",
         traj=f"{RUNS}/S128_T0.160/trajectory.dat",
         top=f"{RUNS}/S128_T0.160/topology.phb",
         title="Seed-size scan S128 T=0.160: big seed melts at high T (PE rises -18.67 -> -18.55)",
         ico_only=False),
    dict(name="twospec_equal_T0.140",
         traj=f"{TWOSPEC}/equal/Kb_300_T_0.140/trajectory.dat",
         top=f"{TWOSPEC}/equal/Kb_300_T_0.140/topology.phb",
         title="2-species EQUAL T=0.140 HERO growth run (PE -37.2 -> -63.2, still running)",
         ico_only=False),
    dict(name="twospec_3H3L_T0.140",
         traj=f"{TWOSPEC}/3H3L/Kb_300_T_0.140/trajectory.dat",
         top=f"{TWOSPEC}/3H3L/Kb_300_T_0.140/topology.phb",
         title="2-species 3H3L T=0.140 growth (PE -37.3 -> -53.2, still running)",
         ico_only=False),
]

JOBS_BATCH1 = [
    dict(name="sweep_ref_a0.10_Ka100_Kb100_str90",
         traj="/scratch/sroy85/Github/dna/large_crystal/sweep/alpha_0.10_Ka_100.0_Kb_100.0_str_90.0/trajectory.dat",
         top="/scratch/sroy85/Github/dna/large_crystal/sweep/alpha_0.10_Ka_100.0_Kb_100.0_str_90.0/input.phb",
         title="PHB large crystal REF (alpha=0.10 Ka=100 Kb=100 str=90, 2048 mol, ICO cores)",
         ico_only=True),
    dict(name="sweep_weak_a0.05_Ka100_Kb100_str1",
         traj="/scratch/sroy85/Github/dna/large_crystal/sweep/alpha_0.05_Ka_100.0_Kb_100.0_str_1.0/trajectory.dat",
         top="/scratch/sroy85/Github/dna/large_crystal/sweep/alpha_0.05_Ka_100.0_Kb_100.0_str_1.0/input.phb",
         title="PHB large crystal WEAK (alpha=0.05 Ka=100 Kb=100 str=1, 2048 mol, ICO cores)",
         ico_only=True),
    dict(name="seeding_S32_T0.150",
         traj="/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/S32_T0.150/trajectory.dat",
         top="/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/S32_T0.150/topology.phb",
         title="PHB seeded growth S32 T=0.150 (500 mol: ICO gold + beads blue)",
         ico_only=False),
]

def ico_indices(top_path):
    idx, order = [], 0
    with open(top_path) as f:
        header = f.readline()
        N = int(header.split()[0])
        for line in f:
            s = line.strip()
            if not s:
                continue
            tok = s.split()[0]
            if tok == "iP" or tok == "iC":
                continue
            if tok == "-3":
                idx.append(order)
            order += 1
    assert order == N, f"particle count mismatch: {order} != {N}"
    return np.array(idx, dtype=np.int64), N

def estimate_frames(traj_path, N):
    sz = os.path.getsize(traj_path)
    with open(traj_path) as f:
        h = [f.readline() for _ in range(3)]
        pl = f.readline()
    per_frame = sum(len(x) for x in h) + len(pl) * N
    return max(1, int(round(sz / per_frame)))

def stream_frames(traj_path, N, stride, max_frames, ico_idx):
    """Yield (step, box, ico_xyz) or (step, box, ico_xyz, bead_xyz)."""
    out, fi = [], 0
    with open(traj_path) as f:
        while len(out) < max_frames:
            l1 = f.readline()
            if not l1:
                break
            l2 = f.readline(); l3 = f.readline()
            if not l3:
                break
            try:
                step = float(l1.split("=")[1])
                box = float(l2.split("=")[1].split()[0])
            except Exception:
                break
            want = (fi % stride == 0)
            fi += 1
            if want:
                pos = np.empty((N, 3))
                for i in range(N):
                    ln = f.readline()
                    p = ln.split()
                    pos[i, 0] = float(p[0]); pos[i, 1] = float(p[1]); pos[i, 2] = float(p[2])
                pos = pos % box
                out.append((step, box, pos))
            else:
                for _ in range(N):
                    f.readline()
    return out

def _render_one(args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    k, nframes, step, box, ico, bead, title, L, png, ico_only = args
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    if ico_only:
        ax.scatter(ico[:, 0], ico[:, 1], ico[:, 2], s=10, c="gold",
                   edgecolors="k", linewidths=0.2, alpha=0.9)
    else:
        ax.scatter(bead[:, 0], bead[:, 1], bead[:, 2], s=1.5, c="steelblue", alpha=0.5)
        ax.scatter(ico[:, 0], ico[:, 1], ico[:, 2], s=22, c="gold",
                   edgecolors="k", linewidths=0.3, alpha=0.95)
    ax.set_xlim(0, L); ax.set_ylim(0, L); ax.set_zlim(0, L)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=20, azim=(k * 360 / max(1, nframes)) % 360)
    ax.set_title(f"{title}\nstep={step:.0f}  frame {k+1}/{nframes}", fontsize=10)
    ax.set_xlabel("x"); ax.set_ylabel("y")
    fig.savefig(png, dpi=90)
    plt.close(fig)
    return png

def render(frames, ico_idx, title, out_mp4, ico_only, box_fixed=None, nproc=None):
    import multiprocessing as mp
    tmpd = os.environ.get("TMPDIR", "/tmp") + "/phb_frames_" + os.path.basename(out_mp4).replace(".mp4", "")
    os.makedirs(tmpd, exist_ok=True)
    mask = np.zeros(frames[0][2].shape[0], dtype=bool)
    mask[ico_idx] = True
    tasks = []
    for k, (step, box, pos) in enumerate(frames):
        ico = pos[mask]
        bead = None if ico_only else pos[~mask]
        tasks.append((k, len(frames), step, box, ico, bead, title, box,
                      os.path.join(tmpd, f"f{k:04d}.png"), ico_only))
    nproc = nproc or int(os.environ.get("SLURM_CPUS_PER_TASK", 0)) or max(1, (os.cpu_count() or 2) - 1)
    print(f"rendering {len(tasks)} frames on {nproc} procs", flush=True)
    with mp.Pool(nproc) as pool:
        pngs = pool.map(_render_one, tasks, chunksize=2)
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    import subprocess
    cmd = [exe, "-y", "-framerate", str(FPS), "-i", os.path.join(tmpd, "f%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", out_mp4]
    subprocess.run(cmd, check=True)
    for p in pngs:
        os.remove(p)
    os.rmdir(tmpd)
    print(f"WROTE {out_mp4} ({os.path.getsize(out_mp4)/1e6:.1f} MB)", flush=True)

def main():
    os.makedirs(VIDDIR, exist_ok=True)
    batch, sel = "batch1", None
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("batch"):
            batch = sys.argv[1]
            sel = int(sys.argv[2]) if len(sys.argv) > 2 else None
        else:
            sel = int(sys.argv[1])
    jobs = JOBS_BATCH2 if batch == "batch2" else JOBS_BATCH1
    jobs = [jobs[sel]] if sel is not None else jobs
    for j in jobs:
        print(f"=== {j['name']} ===", flush=True)
        ico_idx, N = ico_indices(j["top"])
        print(f"N={N} nICO={len(ico_idx)}", flush=True)
        est = estimate_frames(j["traj"], N)
        stride = max(1, est // TARGET_FRAMES)
        print(f"est_frames={est} stride={stride}", flush=True)
        frames = stream_frames(j["traj"], N, stride, TARGET_FRAMES, ico_idx)
        print(f"kept {len(frames)} frames", flush=True)
        out = os.path.join(VIDDIR, j["name"] + ".mp4")
        render(frames, ico_idx, j["title"], out, j["ico_only"])
    print("ALL DONE")

if __name__ == "__main__":
    main()
