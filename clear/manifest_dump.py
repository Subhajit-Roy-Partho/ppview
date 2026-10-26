#!/usr/bin/env python3
"""Dump the run registry of make_visuals.py (the 40 PHB runs of PHB_visuals_2026-10-23) to manifest.json.
Run once from the original location:  python manifest_dump.py /path/to/hand5/final_report  clear/manifest.json
(make_visuals.py resolves run directories relative to its own location, so it must be imported from there)."""
import json, os, sys
src, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, src)
import make_visuals as MV
rows = []
for r in MV.REG.values():
    rows.append(dict(name=r["name"], group=r["group"], label=r["label"], dir=r["dir"], topology=r["top"],
                     initial=r["init"], final=r["final"], headline=r["headline"],
                     initial_exists=os.path.exists(r["init"]), final_exists=os.path.exists(r["final"])))
json.dump(rows, open(out, "w"), indent=1)
print(len(rows), "runs;", sum(not r["final_exists"] or not r["initial_exists"] for r in rows), "with a missing conf")
