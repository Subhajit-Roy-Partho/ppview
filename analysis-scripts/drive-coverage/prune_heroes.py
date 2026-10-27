#!/usr/bin/env python3
"""Keep final.png only in each sweep's highest-yield temperature dir, delete the rest.

Yield source: /tmp/yield_drive.json rows {dir, n, largest, valence, six} computed
with clear/scripts/cluster_labels (see /tmp/yield_drive.py; needs scipy).
Hero per sweep (parent of output/, live tree only): max largest-cluster fraction,
tiebreak max six-valent fraction, then lowest T. Writes yield_heroes.json
(next to this script) and deletes all other final.png (incl. main/ dirs).

Rerun the mass render first if files are missing: render_finals.sh (idempotent).
"""
import json
import os
import subprocess

ROOT = "/mnt/Drive/PHB"
HERE = os.path.dirname(os.path.abspath(__file__))
YIELD_ROWS = "/tmp/yield_drive.json"


def main():
    rows = json.load(open(YIELD_ROWS))
    ok = [r for r in rows if "largest" in r]
    sweeps = {}
    for r in ok:
        d = r["dir"]
        if "/output/" not in d:
            continue
        sweep, t = d.split("/output/", 1)
        if "/Backup/" in sweep:
            continue
        try:
            tval = float(t)
        except ValueError:
            tval = float("inf")
        sweeps.setdefault(sweep, []).append((r, t, tval))
    heroes, table = {}, []
    for sweep, pts in sorted(sweeps.items()):
        pts.sort(key=lambda x: (-x[0]["largest"], -x[0]["six"], x[2]))
        r, t, _ = pts[0]
        heroes[r["dir"]] = r
        table.append(dict(sweep=os.path.relpath(sweep, ROOT), T=t,
                          largest=round(r["largest"], 4), six=round(r["six"], 4),
                          valence=round(r["valence"], 3), n=r["n"]))
    json.dump(table, open(os.path.join(HERE, "yield_heroes.json"), "w"), indent=1)
    print(len(table), "sweep heroes")
    allpng = subprocess.check_output(
        ["find", ROOT, "-name", "final.png", "-not", "-path", "*/Backup/*"],
        text=True).split()
    keep = set(os.path.join(d, "final.png") for d in heroes)
    gone, kept = 0, 0
    for p in allpng:
        if p in keep:
            kept += 1
        else:
            os.remove(p)
            gone += 1
    print(f"kept heroes: {kept}, pruned: {gone}")
    missing = [d for d in heroes if not os.path.isfile(os.path.join(d, "final.png"))]
    print("heroes missing final.png:", len(missing))
    for m in missing:
        print(" ", m)


if __name__ == "__main__":
    main()
