#!/usr/bin/env python3
"""Web-size assets for oxDNAcpp gh-pages PHB/visuals: images (jpg), videos (854x480 h264 + poster), mgl zips."""
import json, os, subprocess, sys, zipfile, glob
from pathlib import Path
from PIL import Image
OUT = Path("/scratch/sroy85/Github/dna/large_crystal/PHB_visuals_2026-10-23")
DST = Path(sys.argv[1]); (DST / "img").mkdir(parents=True, exist_ok=True); (DST / "vid").mkdir(exist_ok=True); (DST / "dl").mkdir(exist_ok=True)
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
idx = json.load(open(OUT / "index.json"))
def jpg(src, dst, w=1600, q=82):
    im = Image.open(src).convert("RGB")
    if im.width > w: im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    im.save(dst, quality=q, optimize=True)
n_img = 0
for r in idx:
    n = r["name"]
    jpg(OUT / "images" / f"{n}_initial_vs_final.jpg", DST / "img" / f"{n}_initial_vs_final.jpg", 1800, 80)
    for im in r["images"]:
        if "_slab" in im and im.endswith(".png"):
            jpg(OUT / "images" / im, DST / "img" / im.replace(".png", ".jpg"), 1500, 80); n_img += 1
for f in ("ka_alpha", "two_species_vs_T", "timecourses_headline"):
    jpg(OUT / "analysis" / f"{f}.png", DST / "img" / f"{f}.jpg", 1800, 88)
for r in idx:
    for ph in ("initial", "final"):
        if r["name"] in ("crystal_Kb300_T0.100",) or r["name"].startswith("seed_S256_T0.140_r1"):
            jpg(OUT / "images" / f"{r['name']}_{ph}_iso.png", DST / "img" / f"{r['name']}_{ph}_iso.jpg", 1600, 82)
def venc(src, dst):
    if dst.exists(): return
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(src), "-vf", "scale=854:-2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "29", "-preset", "slow", "-movflags", "+faststart", str(dst)], check=True)
    subprocess.run([FF, "-y", "-loglevel", "error", "-sseof", "-0.3", "-i", str(src), "-frames:v", "1", "-vf", "scale=854:-2", "-q:v", "4", str(dst.with_suffix(".jpg"))], check=True)
tot = 0
for p in sorted((OUT / "videos").glob("*.mp4")):
    d = DST / "vid" / p.name; venc(p, d); tot += d.stat().st_size
print("videos MB", tot / 1e6)
# mgl zips
def zipit(name, files):
    with zipfile.ZipFile(DST / "dl" / name, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files: z.write(OUT / "mgl" / f, f)
    print(name, round((DST / "dl" / name).stat().st_size / 1e6, 1), "MB", len(files), "files")
allsp = sorted(os.path.basename(p) for p in glob.glob(str(OUT / "mgl" / "*_species.mgl")))
zipit("PHB_mgl_species_all_runs.zip", allsp)
head = [r["name"] for r in idx if r["group"] and any(k in r["name"] for k in ("2sp_3H3L_T0.140", "2sp_5L1H_T0.140", "4sp_ww_T0.140", "seed_S128_T0.140_r2", "seed_S256_T0.140_r1", "seed_S256_T0.140_r2", "crystal_Kb300_T0.100", "2sp_highT_3H3L_T0.170", "Ka30_a0.10"))]
zipit("PHB_mgl_patches_headline_runs.zip", sorted(f"{n}_{ph}_patches.mgl" for n in head for ph in ("initial", "final")))
