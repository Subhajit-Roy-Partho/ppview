#!/usr/bin/env python3
"""PHB visual deliverables: initial/final snapshots -> .mgl (cogli), images, montages, videos, metrics.

  make_visuals.py snap [NAME..]     copy initial/final confs + topologies into OUT/confs, OUT/topologies
  make_visuals.py mgl  [NAME..]     OUT/mgl/<name>_{initial,final}_{patches,species}.mgl  (molecule-wrapped, oxDNAcpp converter + species writer)
  make_visuals.py img  [NAME..]     OUT/images/<name>_{initial,final}_{iso,close}.png, slab views, <name>_initial_vs_final.png, metrics json
  make_visuals.py vid  NAME|INDEX   OUT/videos/<name>.mp4 (helix bundles, species colours, six-valent + cluster highlighting) [Slurm array]
  make_visuals.py turn NAME         OUT/videos/<name>_turntable.mp4 (rotating final configuration)
  make_visuals.py list
"""
import json, os, subprocess, sys, shutil, tempfile, time
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import cluster_labels as CL
import render_species as RS
from make_videos import frame_index

R = HERE.parent
OUT = Path("/scratch/sroy85/Github/dna/large_crystal/PHB_visuals_2026-10-23")
TERMINAL = "/scratch/sroy85/Github/oxDNAcpp/main/src/build/terminal"
FF = None
REG = {}

def add(name, group, label, rundir, headline=False, top=None, init=None, zoom=1.0, vzoom=None):
    d = Path(rundir) if str(rundir).startswith("/") else R / rundir
    t = Path(os.path.realpath(top or d / "topology.phb"))
    i = d / (init or ("mc_relaxed.dat" if (d / "mc_relaxed.dat").exists() else "start_conf.dat"))
    REG[name] = dict(name=name, group=group, label=label, dir=str(d), top=str(t), init=str(i), final=str(d / "final_conf.dat"),
                     traj=str(d / "trajectory.dat"), headline=headline, zoom=zoom)

TS = "two_species_preconnected"
for v, lab in (("equal", "equal (6 strong)"), ("5H1L", "5-1 (5 strong + 1 weak)"), ("3H3L", "3-3 (3 strong + 3 weak)"), ("5L1H", "1-5 (1 strong + 5 weak)")):
    add(f"2sp_{v}_T0.140", "2-species, T = 0.14", f"2-species {lab}, T=0.14", f"{TS}/{v}/Kb_300_T_0.140", headline=v in ("3H3L", "5L1H"))
for v in ("3H3L", "5L1H"):
    add(f"2sp_{v}_T0.078", "2-species, T = 0.078 (stopped)", f"2-species {v}, T=0.078", f"{TS}/{v}/Kb_300_T_0.078")
for v in ("3H3L", "5L1H"):
    for T in ("0.150", "0.160", "0.170", "0.180"):
        add(f"2sp_highT_{v}_T{T}", "2-species, higher T", f"2-species {v}, T={T}, 32-molecule seed", f"seeding_scan/runs/TS_{v}_T{T}", headline=(v == "3H3L" and T == "0.170"))
add("4sp_ww_T0.140", "4-species preconnected", "4-species weak-weak (K=2), T=0.14, 32-seed", "preconnected_K300_large/weak_weak/Kb_300_T_0.140", headline=True)
add("4sp_ws_T0.140", "4-species preconnected", "4-species weak-strong (K~101), T=0.14, 32-seed", "preconnected_K300_large/weak_strong/Kb_300_T_0.140")
add("4sp_ww_T0.078", "4-species preconnected", "4-species weak-weak (K=2), T=0.078, 32-seed", "preconnected_K300_large/weak_weak/Kb_300_T_0.078")
add("4sp_seed8_ws_T0.140", "4-species preconnected", "4-species weak-strong, 8-seed, T=0.14", "preconnected_seed_sweep/four_species/Kb_300_T_0.140")
for rn, hl in (("S8_T0.140", 0), ("S8_T0.160", 0), ("S32_T0.150", 0), ("S64_T0.140", 0), ("S128_T0.140_r2", 1), ("S128_T0.150", 0), ("S128_T0.160", 0),
               ("S192_T0.140_r1", 0), ("S256_T0.140_r1", 1), ("S256_T0.140_r2", 0)):
    add(f"seed_{rn}", "Seeded growth (4-species, K=2)", f"seed {rn.split('_')[0][1:]} molecules, T={rn.split('_')[1][1:]}", f"seeding_scan/runs/{rn}", headline=bool(hl))
for ka in ("10", "30", "100", "300", "1000"):
    for a in ("0.10", "0.12"):
        if ka == "300" and a == "0.10": continue
        add(f"Ka{ka}_a{a}", "Ka x alpha study (S128, T=0.14)", f"Ka={ka}, alpha={a}", f"seeding_scan/runs/KA_S128_T0.140_Ka{ka}_a{a}")
add("window_Q_T0.140", "Melt-quench", "melt at T=0.17 then hold T=0.14", "window_scan/runs/Q_T0.140_a")
for kb in ("1", "300"):
    add(f"crystal_Kb{kb}_T0.100", "Pre-formed crystal (2048 molecules)", f"pre-formed crystal, weak-weak K=2, Kb={kb}, T=0.10", f"stiffness_sweep/weak_weak/Kb_{kb}_T_0.100", headline=(kb == "300"), zoom=1.0)
CRYSTAL = lambda n: n.startswith("crystal_")

def paths(r, phase):
    return (r["init"] if phase == "initial" else r["final"])

def sel(names):
    return [REG[n] for n in names] if names else list(REG.values())

def mol_wrapped(topo, conf):
    t, box, pos, a1, a3 = CL.load_conf(conf, topo["N"])
    return t, box, RS.wrap_molecules(topo, pos, box), pos

def metrics(topo, conf):
    t, box, pos, a1, a3 = CL.load_conf(conf, topo["N"])
    res = CL.analyze_conf(topo, conf=(t, box, pos, a1, a3))
    n = topo["n_mol"]; val = res["valence"]
    cl = CL.clique_stats(topo, res["neighbors"]) if n < 3000 else {}
    return res, dict(step=float(t), n_molecules=int(n), largest_cluster=float((res["mol_label"] == 0).sum() / n), n_clusters=int(res["mol_label"].max() + 1),
                     mean_valence=float(val.mean()), six_valent=float((val == 6).mean()), tetra_per_molecule=float(cl.get("n_tetra", 0) / n) if cl else None)

def do_snap(r):
    (OUT / "confs").mkdir(parents=True, exist_ok=True)
    for ph in ("initial", "final"):
        dst = OUT / "confs" / f"{r['name']}_{ph}.dat"
        for _ in range(4):
            shutil.copyfile(paths(r, ph), dst)
            n = int(open(r["top"]).readline().split()[0])
            if sum(1 for _ in open(dst)) >= n + 3: break
            time.sleep(3)
    dt = OUT / "topologies" / (Path(r["top"]).parent.name + "__" + Path(r["top"]).name)
    dt.parent.mkdir(parents=True, exist_ok=True)
    if not dt.exists(): shutil.copyfile(r["top"], dt)
    return r["name"]

def read_topo(r):
    return CL.load_topology(r["top"])

def write_mgl_species(topo, conf, res, path):
    t, box, pos_w, _ = mol_wrapped(topo, conf)
    rgb = RS.particle_colours(topo, res, int(topo["species"].max()) + 1)
    rad = np.where(topo["ptype"] == -3, 1.0, 0.1)
    p = pos_w - box / 2.0
    with open(path, "w") as f:
        f.write(f".Box:{box[0]:g},{box[1]:g},{box[2]:g}\n")
        for i in range(topo["N"]):
            c = (np.clip(rgb[i], 0, 1) * 255).astype(int)
            f.write(f"{p[i,0]:.6f} {p[i,1]:.6f} {p[i,2]:.6f} @ {rad[i]:g} C[{c[0]},{c[1]},{c[2]},1]\n")

def do_mgl(r):
    topo = read_topo(r); (OUT / "mgl").mkdir(parents=True, exist_ok=True)
    for ph in ("initial", "final"):
        conf = str(OUT / "confs" / f"{r['name']}_{ph}.dat")
        t, box, pos_w, pos_raw = mol_wrapped(topo, conf)
        raw = OUT / "mgl" / f".{r['name']}_{ph}_raw.mgl"
        subprocess.run([TERMINAL, "autoconvert", "-i", r["top"], "-d", conf, "-o", str(raw)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        lines = open(raw).read().splitlines()
        assert len(lines) == topo["N"] + 1, (len(lines), topo["N"])
        p = pos_w - box / 2.0
        outp = OUT / "mgl" / f"{r['name']}_{ph}_patches.mgl"
        with open(outp, "w") as f:
            f.write(f".Box:{box[0]:g},{box[1]:g},{box[2]:g}\n")
            for i, ln in enumerate(lines[1:]):
                rest = ln.split(" ", 3)[3]
                f.write(f"{p[i,0]:.6f} {p[i,1]:.6f} {p[i,2]:.6f} {rest}\n")
        raw.unlink()
        res = CL.analyze_conf(topo, conf_path=conf)
        write_mgl_species(topo, conf, res, OUT / "mgl" / f"{r['name']}_{ph}_species.mgl")
    return r["name"]

def topo_box(conf):
    return CL.load_conf(conf)[1][0]

def slab_for(topo, res, conf, ax, thick):
    """(axis, lo, hi) slab of `thick` length units through the centre of the largest cluster (circular mean, periodic-safe)."""
    t, box, pos, a1, a3 = CL.load_conf(conf, topo["N"])
    k = "xyz".index(ax); L = box[k]
    cores = topo["cores"][res["mol_label"] == 0]
    th = 2 * np.pi * np.mod(pos[cores, k], L) / L
    c = np.mod(np.arctan2(np.sin(th).mean(), np.cos(th).mean()) * L / (2 * np.pi), L)
    return (ax, max(0.0, (c - thick / 2) / L), min(1.0, (c + thick / 2) / L))

def cap_img(path, text):
    im = Image.open(path).convert("RGB"); d = ImageDraw.Draw(im)
    return im

def do_img(r):
    topo = read_topo(r); (OUT / "images").mkdir(parents=True, exist_ok=True)
    cryst = CRYSTAL(r["name"]); out = {}
    for ph in ("initial", "final"):
        conf = str(OUT / "confs" / f"{r['name']}_{ph}.dat")
        res, m = metrics(topo, conf); out[ph] = m
        lab = f"{r['label']} - {ph} (step {m['step']:.3g})  cluster {100*m['largest_cluster']:.0f}%  six-valent {100*m['six_valent']:.1f}%  valence {m['mean_valence']:.2f}"
        W, Hh = (2560, 1440) if cryst else (1920, 1080)
        RS.render_conf(r["top"], conf, str(OUT / "images" / f"{r['name']}_{ph}_iso.png"), W, Hh, "iso", None, lab, True, cryst, 1.0, fit="box", topo=topo, res=res)
        RS.render_conf(r["top"], conf, str(OUT / "images" / f"{r['name']}_{ph}_close.png"), W, Hh, "iso", None, lab, True, cryst, 1.0, box=False, fit="auto", topo=topo, res=res)
        if cryst or r["headline"]:
            for ax in ("x", "y", "z"):
                sl = slab_for(topo, res, conf, ax, 7.0 if cryst else 10.0)
                RS.render_conf(r["top"], conf, str(OUT / "images" / f"{r['name']}_{ph}_slab{ax}.png"), W, Hh, ax, sl,
                               f"{r['label']} - {ph} - {sl[2]*0+ (sl[2]-sl[1])*topo_box(conf):.0f}-unit slab viewed along {ax}", True, False, 1.0, box=False, fit="auto", topo=topo, res=res, fit_cluster=0)
    # side-by-side
    a = Image.open(OUT / "images" / f"{r['name']}_initial_close.png"); b = Image.open(OUT / "images" / f"{r['name']}_final_close.png")
    w = min(a.width, 1400); a = a.resize((w, int(a.height * w / a.width))); b = b.resize((w, int(b.height * w / b.width)))
    M = Image.new("RGB", (2 * w + 30, a.height + 20), "white"); M.paste(a, (10, 10)); M.paste(b, (w + 20, 10))
    M.save(OUT / "images" / f"{r['name']}_initial_vs_final.jpg", quality=90)
    json.dump(dict(name=r["name"], group=r["group"], label=r["label"], **out), open(OUT / "images" / f"{r['name']}.metrics.json", "w"), indent=1)
    return r["name"]

# ----------------------------------------------------------------------------- video
_W = {}
def _init(top):
    _W["topo"] = CL.load_topology(top)

def _frame(a):
    k, text, top, mode, label, width, height, tmp, zoom, azim = a
    topo = _W["topo"]
    t, box, pos, a1, a3 = CL.parse_frame_text(text)
    res = CL.analyze_conf(topo, conf=(t, box, pos, a1, a3))
    n = topo["n_mol"]; val = res["valence"]
    cap = f"{label} | step {t:.2e} | cluster {100*(res['mol_label']==0).sum()/n:.0f}% | six-valent {100*(val==6).mean():.1f}% | valence {val.mean():.2f}"
    conf = f"{tmp}/c{k:05d}.dat"; open(conf, "w").write(text); png = f"{tmp}/f{k:05d}.png"
    RS.render_conf(top, conf, png, width, height, "iso", None, cap, True, False, zoom, box=True, fit="box", azim=azim, topo=topo, res=res)
    os.remove(conf)
    return dict(step=float(t), largest=float((res["mol_label"] == 0).sum() / n), six=float((val == 6).mean()), valence=float(val.mean()))

def encode(tmp, out, fps, scale_w=None, crf=23):
    global FF
    FF = FF or __import__("imageio_ffmpeg").get_ffmpeg_exe()
    vf = ["-vf", f"scale={scale_w}:-2"] if scale_w else []
    subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{tmp}/f%05d.png"] + vf + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), str(out)], check=True)

def do_vid(r, frames=150, fps=15, procs=None, width=1280, height=720):
    (OUT / "videos").mkdir(parents=True, exist_ok=True)
    t0 = time.time(); idx, nraw, med = frame_index(r["traj"])
    sel_i = np.unique(np.linspace(0, len(idx) - 1, min(frames, len(idx))).round().astype(int))
    texts = []
    with open(r["traj"], "rb") as f:
        for i in sel_i:
            s, e = idx[i]; f.seek(s); texts.append(f.read(e - s).decode())
    tmp = tempfile.mkdtemp(prefix="vid_", dir=os.environ.get("TMPDIR", "/tmp"))
    zoom = 1.0
    tasks = [(k, tx, r["top"], None, r["label"], width, height, tmp, zoom, None) for k, tx in enumerate(texts)]
    procs = procs or int(os.environ.get("SLURM_CPUS_PER_TASK", 4))
    with Pool(procs, initializer=_init, initargs=(r["top"],)) as pool:
        rows = pool.map(_frame, tasks, chunksize=1)
    out = OUT / "videos" / f"{r['name']}.mp4"; encode(tmp, out, fps)
    steps = [x["step"] for x in rows]
    json.dump(dict(name=r["name"], frames=len(rows), complete_frames_in_file=len(idx), dropped_incomplete=nraw - len(idx), first_step=steps[0], last_step=steps[-1],
                   monotonic=bool(np.all(np.diff(steps) >= 0)), per_frame=rows, seconds=round(time.time() - t0)), open(OUT / "videos" / f"{r['name']}.json", "w"))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"WROTE {out} {out.stat().st_size/1e6:.1f} MB steps {steps[0]:.3g}..{steps[-1]:.3g} in {time.time()-t0:.0f}s", flush=True)

def do_turn(r, frames=72, fps=12):
    topo = read_topo(r); conf = str(OUT / "confs" / f"{r['name']}_final.dat"); res, m = metrics(topo, conf)
    tmp = tempfile.mkdtemp(prefix="turn_", dir=os.environ.get("TMPDIR", "/tmp")); cryst = CRYSTAL(r["name"])
    for k in range(frames):
        RS.render_conf(r["top"], conf, f"{tmp}/f{k:05d}.png", 1280, 720, "iso", None, f"{r['label']} - final, six-valent {100*m['six_valent']:.1f}%", True, cryst, 1.0,
                       box=True, fit="box", azim=k * 360 / frames, topo=topo, res=res)
    out = OUT / "videos" / f"{r['name']}_turntable.mp4"; encode(tmp, out, fps); shutil.rmtree(tmp, ignore_errors=True); print("WROTE", out)

STAGES = dict(snap=do_snap, mgl=do_mgl, img=do_img)
if __name__ == "__main__":
    st = sys.argv[1]; names = sys.argv[2:]
    if st == "list":
        for i, n in enumerate(REG): print(i, n, "HEADLINE" if REG[n]["headline"] else "")
    elif st in ("vid", "turn"):
        r = REG[names[0]] if names[0] in REG else list(REG.values())[int(names[0])]
        (do_vid if st == "vid" else do_turn)(r)
    else:
        os.nice(8)
        with Pool(int(os.environ.get("PROCS", 6))) as pool:
            for n in pool.imap_unordered(STAGES[st], sel(names)): print("ok", st, n, flush=True)
