#!/usr/bin/env python3
"""
render_batch.py - render every entry of a manifest.json with render_phb.py.

Manifest: either a top-level list of entries or an object holding the list under
"entries" (or "runs" / "systems" / "items"). Each entry needs a topology and a
configuration; labels (a per-particle cluster label file) are optional:

    topology : topology | top | topology_file
    conf     : conf | config | conf_snapshot | conf_file | final_conf
    labels   : labels | cluster_file | labels_file
    name     : name | id | (system + "__" + run, slashes replaced by "_")

Usage:
    python render_batch.py manifest.json --outdir renders/ [render_phb options...]

Any option render_phb.py understands (--width, --cores-only, --legend, --view,
...) is passed through to every render. Entries with labels get cluster colouring
(and --legend/--highlight-largest if given); entries without get patch colouring.
Relative paths are resolved against the manifest's directory. One failing entry
does not stop the batch; the exit status is non-zero if any failed.
"""
import argparse
import json
import os
import re
import sys
import time
import traceback

import render_phb

TOP_KEYS = ("topology", "top", "topology_file")
CONF_KEYS = ("conf", "config", "conf_snapshot", "conf_file", "final_conf")
LABEL_KEYS = ("labels", "cluster_file", "labels_file")
LIST_KEYS = ("entries", "runs", "systems", "items")


def first(entry, keys):
    for k in keys:
        if entry.get(k):
            return entry[k]
    return None


def load_entries(path):
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        for k in LIST_KEYS:
            if isinstance(data.get(k), list):
                return data[k]
        lists = [v for v in data.values() if isinstance(v, list) and v and isinstance(v[0], dict)]
        if lists:
            return lists[0]
        raise SystemExit(f"{path}: no list of entries found")
    return data


def entry_name(entry, index):
    name = first(entry, ("name", "id"))
    if not name:
        system, run = str(entry.get("system") or ""), str(entry.get("run") or "")
        if run.startswith(system + "/"):        # run paths often repeat the system
            system = ""
        parts = [p for p in (system, run) if p]
        name = "__".join(parts) if parts else f"entry{index:03d}"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 add_help=True)
    ap.add_argument("manifest")
    ap.add_argument("--outdir", default="renders")
    ap.add_argument("--only", default=None, help="only entries whose name contains this text")
    ap.add_argument("--skip-existing", action="store_true")
    args, passthrough = ap.parse_known_args(argv)

    base = os.path.dirname(os.path.abspath(args.manifest))
    entries = load_entries(args.manifest)
    os.makedirs(args.outdir, exist_ok=True)

    def resolve(p):
        return p if os.path.isabs(p) else os.path.join(base, p)

    failed = 0
    for i, entry in enumerate(entries):
        name = entry_name(entry, i)
        if args.only and args.only not in name:
            continue
        top, conf, labels = first(entry, TOP_KEYS), first(entry, CONF_KEYS), first(entry, LABEL_KEYS)
        if not top or not conf:
            print(f"[{i}] {name}: missing topology/conf, skipped", file=sys.stderr)
            failed += 1
            continue
        out = os.path.join(args.outdir, name + ".png")
        if args.skip_existing and os.path.exists(out):
            continue
        argv_i = ["--top", resolve(top), "--conf", resolve(conf), "--out", out]
        if labels and os.path.exists(resolve(labels)):
            argv_i += ["--cluster-file", resolve(labels)]
        argv_i += passthrough
        if "--title" not in passthrough:
            argv_i += ["--title", name]
        t0 = time.time()
        try:
            render_phb.main(argv_i + ["--quiet"])
            print(f"[{i}] {name}: {out} ({time.time() - t0:.1f}s)", flush=True)
        except (Exception, SystemExit) as exc:        # keep going
            failed += 1
            print(f"[{i}] {name}: FAILED: {exc}", file=sys.stderr)
            if not isinstance(exc, SystemExit):
                traceback.print_exc()
    print(f"done: {len(entries) - failed} ok, {failed} failed -> {args.outdir}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
