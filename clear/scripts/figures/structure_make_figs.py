"""PNG figures from results/*.json. Run: python3 code/make_figs.py"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RESULTS, FIGS

os.makedirs(FIGS, exist_ok=True)
LABELS = ["ref500", "S256_r1", "S256_r2", "S192_r1", "S128_r2", "KA30",
          "KA100", "PC4ww", "PC4ws_gel", "TS3H3L"]
PRETTY = {"ref500": "ref500 (finite perfect)", "S256_r1": "S256 T0.140 r1",
          "S256_r2": "S256 T0.140 r2", "S192_r1": "S192 T0.140 r1",
          "S128_r2": "S128 T0.140 r2", "KA30": "Ka30 a0.10",
          "KA100": "Ka100 a0.12", "PC4ww": "4sp 32seed T0.140",
          "PC4ws_gel": "gel control", "TS3H3L": "2-species 3H3L"}


def fig_powder():
    fig, ax = plt.subplots(figsize=(9, 6))
    sq0 = json.load(open(os.path.join(RESULTS, "sq_ref500.json")))
    lines = sq0["ideal_lines"]
    for ln in lines[:7]:
        ax.axvline(ln["q"], color="k", ls=":", alpha=0.5)
        ax.text(ln["q"], 4.6, "(%d%d%d)" % tuple(ln["hkl"]), rotation=90,
                fontsize=7, ha="right", va="top")
    for i, lab in enumerate(LABELS):
        r = json.load(open(os.path.join(RESULTS, f"sq_{lab}.json")))
        q = np.array(r["powder"]["q"])
        s = np.array(r["powder"]["S"])
        m = (q >= 0.5) & (q <= 6.0)
        ax.plot(q[m], s[m] + i * 0.9, lw=1, label=PRETTY[lab])
    ax.set_xlabel("q (1/sim unit)")
    ax.set_ylabel("S(q) powder + offset")
    ax.set_title("Debye powder patterns of largest clusters (offset stacked); "
                 "dotted = ideal Fd-3m lines")
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "powder_all.png"), dpi=150)
    plt.close(fig)


def fig_qbar():
    panels = ["ref500", "S256_r2", "S128_r2", "PC4ws_gel"]
    fig, axs = plt.subplots(2, 2, figsize=(9, 8), sharex=True, sharey=True)
    for ax, lab in zip(axs.ravel(), panels):
        g = json.load(open(os.path.join(RESULTS, f"grains_{lab}.json")))
        x = np.array(g["q4bar"])
        y = np.array(g["q6bar"])
        like = np.array(g["crystal_like"])
        ax.scatter(x[~like], y[~like], s=4, c="0.6", label="other")
        ax.scatter(x[like], y[like], s=4, c="C0", label="crystal-like")
        th = plt.Circle((0.1941, 0.5553), 0.12, fill=False, ec="r", lw=1.5)
        ax.add_patch(th)
        ax.set_title(f"{PRETTY[lab]}: xtal frac={g['frac_crystal_like']:.2f}")
        ax.set_xlim(-0.05, 0.6)
        ax.set_ylim(-0.05, 0.8)
    for ax in axs.ravel():
        ax.set_xlabel("q4bar")
        ax.set_ylabel("q6bar")
    axs[0, 0].legend(fontsize=8)
    fig.suptitle("Local bond-orientational order (red circle = crystal-like region)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "qbar_scatter.png"), dpi=150)
    plt.close(fig)


def fig_misori():
    fig, ax = plt.subplots(figsize=(8, 5))
    for lab in ["ref500", "S256_r2", "S192_r1", "PC4ww"]:
        g = json.load(open(os.path.join(RESULTS, f"grains_{lab}.json")))
        h = np.array(g["misorientation"]["hist"])
        e = np.array(g["misorientation"]["edges_hist"])
        c = 0.5 * (e[1:] + e[:-1])
        ax.step(c, h / h.sum(), where="mid", label=f"{PRETTY[lab]}")
    ax.axvline(10, color="k", ls="--", label="grain threshold 10 deg")
    ax.set_xlabel("bonded-neighbour misorientation (deg, symmetry-reduced)")
    ax.set_ylabel("fraction of edges")
    ax.set_title("Misorientation distributions: all peak ~40-45 deg "
                 "(random-frame value); no <10 deg population")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "misorientation_hist.png"), dpi=150)
    plt.close(fig)


def fig_defects():
    order = ["perfect-bulk", "surface", "vacancy-adjacent", "missing-bridge",
             "wrong-partner", "interstitial", "grain-boundary", "gas/free"]
    labs = ["pref_mc*", "pref_final*", "S256_r1", "S256_r2", "S192_r1",
            "S128_r2", "KA30", "KA100", "PC4ww", "PC4ws_gel", "TS3H3L"]
    files = ["pref_mc", "pref_final", "S256_r1", "S256_r2", "S192_r1",
             "S128_r2", "KA30", "KA100", "PC4ww", "PC4ws_gel", "TS3H3L"]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bottom = np.zeros(len(files))
    for cls in order:
        vals = []
        for f in files:
            d = json.load(open(os.path.join(RESULTS, f"defects_{f}.json")))
            ncl = d["n_cluster"]
            vals.append(d["counts"][cls] / ncl)
        ax.bar(labs, vals, bottom=bottom, label=cls)
        bottom += np.array(vals)
    ax.set_ylabel("fraction of largest-cluster members (*=of 1452/1503)")
    ax.set_title("Defect census per run (first match wins; classes in methods)")
    ax.legend(fontsize=8, ncol=2)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "defect_bars.png"), dpi=150)
    plt.close(fig)


def fig_rank():
    labs = ["ref500", "S256_r2", "S256_r1", "S192_r1", "KA30", "PC4ww",
            "S128_r2", "KA100", "PC4ws_gel", "TS3H3L"]
    xtal, bulk = [], []
    for lab in labs:
        g = json.load(open(os.path.join(RESULTS, f"grains_{lab}.json")))
        xtal.append(g["frac_crystal_like"])
        if lab == "ref500":
            bulk.append(0.992)  # measured: patch census on prefmc restricted
            # to ref500 members with coord==6 (491/495 perfect-bulk)
        else:
            d = json.load(open(os.path.join(RESULTS, f"defects_{lab}.json")))
            bulk.append(d["bulk_defectfree_frac"])
    x = np.arange(len(labs))
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(x - 0.2, xtal, 0.4, label="crystal-like cores / cluster cores")
    ax.bar(x + 0.2, bulk, 0.4, label="defect-free bulk / bulk (coord==6)")
    ax.set_xticks(x)
    ax.set_xticklabels(labs, rotation=25, ha="right")
    ax.set_ylabel("fraction of ideal")
    ax.set_title("Fraction-of-ideal-crystal ranking (surface effects subtracted "
                 "in the bulk metric)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "fraction_ideal.png"), dpi=150)
    plt.close(fig)


def fig_spatial():
    """Grain-map spatial view: largest-cluster cores, xy+xz, coloured by
    class (perfect-bulk / surface / other defect). No grains exist
    (all <=2 members at <10 deg), so this doubles as the grain map:
    a single crystal would be one colour; polycrystal would show
    domains. Best run + reference shown."""
    import sys
    sys.path.insert(0, "/scratch/sroy85/Github/dna/large_crystal/phase_diagram/analysis")
    from common import load_run, unwrap_cluster
    from phasekit import structure as St
    fig, axs = plt.subplots(2, 2, figsize=(10, 9))
    for row, lab in enumerate(["ref500", "S256_r2"]):
        if lab == "ref500":
            z = np.load("data/ref500.npz")
            sub = np.asarray(z["cores"])
            like = np.array(json.load(open(os.path.join(RESULTS, "grains_ref500.json")))["crystal_like"])
            cls = np.array(["perfect-bulk" if l else "other" for l in like])
        else:
            topo, conf, res, cpos = load_run(lab)
            t, box, pos, a1, a3 = conf
            big = int(np.argmax(res["comp_sizes"]))
            members = np.where(res["comp"] == big)[0]
            uw, order = unwrap_cluster(cpos, box, res["bonds"]["mol_a"],
                                       res["bonds"]["mol_b"], members)
            sub = np.array([uw[m] for m in order])
            dd = json.load(open(os.path.join(RESULTS, f"defects_{lab}.json")))
            cls = np.array([dd["classes"][str(m)] for m in order])
        col = {"perfect-bulk": "C0", "surface": "C1"}.get
        c = [col(x, "0.5") for x in cls]
        axs[row, 0].scatter(sub[:, 0], sub[:, 1], s=6, c=c)
        axs[row, 0].set_title(f"{lab}: xy (blue=perfect, orange=surface, grey=defect)")
        axs[row, 0].set_aspect("equal")
        axs[row, 1].scatter(sub[:, 0], sub[:, 2], s=6, c=c)
        axs[row, 1].set_title(f"{lab}: xz")
        axs[row, 1].set_aspect("equal")
    fig.suptitle("Spatial (grain) maps: no orientation domains; defects scattered, "
                 "not clustered at boundaries")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "grainmap_spatial.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    fig_powder()
    fig_qbar()
    fig_misori()
    fig_defects()
    fig_rank()
    fig_spatial()
    print("wrote", sorted(os.listdir(FIGS)))
