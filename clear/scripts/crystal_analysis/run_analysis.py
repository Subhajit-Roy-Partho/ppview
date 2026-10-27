#!/usr/bin/env python3
"""
Batch crystal analysis for all hand5 PHB simulations.
Runs analyze_phb_crystal.py in parallel and saves results to results.json.
"""
import json
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

LARGE_CRYSTAL = Path(__file__).parent.parent
ANALYSIS_SCRIPT = LARGE_CRYSTAL / "analyze_phb_crystal.py"
PYTHON = sys.executable
OUTPUT = Path(__file__).parent / "results.json"

def discover_dirs():
    """Return list of (label, sweep, patch_set, Kb, T, top_path, conf_path)."""
    dirs = []

    # stiffness_sweep and seeded_sweep
    for sweep in ("stiffness_sweep", "seeded_sweep"):
        for pset in ("weak_weak", "weak_strong"):
            base = LARGE_CRYSTAL / "hand5" / sweep / pset
            for d in sorted(base.iterdir()):
                m = re.match(r"Kb_(\d+)_T_([0-9.]+)", d.name)
                if not m:
                    continue
                kb, T = int(m.group(1)), float(m.group(2))
                top = d / "topology.phb"
                conf = d / "final_conf.dat"
                if not top.exists() or not conf.exists():
                    print(f"  SKIP (missing files): {d}", file=sys.stderr)
                    continue
                dirs.append({
                    "label": f"{sweep}/{pset}/{d.name}",
                    "sweep": sweep,
                    "patch_set": pset,
                    "Kb": kb,
                    "T": T,
                    "top": str(top),
                    "conf": str(conf),
                })

    # preconnected_seed_sweep
    base = LARGE_CRYSTAL / "hand5" / "preconnected_seed_sweep" / "four_species"
    for d in sorted(base.iterdir()):
        m = re.match(r"Kb_(\d+)_T_([0-9.]+)", d.name)
        if not m:
            continue
        kb, T = int(m.group(1)), float(m.group(2))
        top = d / "topology.phb"
        conf = d / "final_conf.dat"
        if not top.exists() or not conf.exists():
            print(f"  SKIP (missing files): {d}", file=sys.stderr)
            continue
        dirs.append({
            "label": f"preconnected/{d.name}",
            "sweep": "preconnected",
            "patch_set": "four_species",
            "Kb": kb,
            "T": T,
            "top": str(top),
            "conf": str(conf),
        })

    return dirs


def run_one(entry):
    cmd = [
        PYTHON, str(ANALYSIS_SCRIPT),
        "--top", entry["top"],
        "--conf", entry["conf"],
        "--json",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        # Extract JSON block from output (after the progress lines)
        stdout = result.stdout
        # Find the last top-level '{' (on its own line) to skip nested braces in val_counts
        lines = stdout.split("\n")
        json_start_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "{":
                json_start_idx = i
        if json_start_idx is None:
            raise RuntimeError(f"no JSON block in output: {stdout[:300]}")
        crystal = json.loads("\n".join(lines[json_start_idx:]))
        entry["crystal"] = crystal
        entry["ok"] = True
    except Exception as e:
        entry["crystal"] = {}
        entry["ok"] = False
        entry["error"] = str(e)
    return entry


def main():
    print("Discovering simulation directories...")
    dirs = discover_dirs()
    print(f"Found {len(dirs)} simulation directories to analyze")

    results = []
    n_ok = 0
    n_fail = 0

    with ProcessPoolExecutor(max_workers=16) as ex:
        futures = {ex.submit(run_one, d): d["label"] for d in dirs}
        for i, fut in enumerate(as_completed(futures), 1):
            label = futures[fut]
            try:
                r = fut.result()
                results.append(r)
                status = "OK" if r["ok"] else f"FAIL: {r.get('error','')}"
                lc = r["crystal"].get("largest_cluster_fraction", 0) * 100 if r["ok"] else 0
                print(f"  [{i:3d}/{len(dirs)}] {label}: {status}  LC={lc:.1f}%")
                if r["ok"]:
                    n_ok += 1
                else:
                    n_fail += 1
            except Exception as e:
                print(f"  [{i:3d}/{len(dirs)}] {label}: EXCEPTION {e}")
                n_fail += 1

    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone: {n_ok} OK, {n_fail} failed")
    print(f"Results saved to {OUTPUT}")


if __name__ == "__main__":
    main()
