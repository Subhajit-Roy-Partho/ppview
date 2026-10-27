#!/usr/bin/env python3
"""Generate oxDNAcpp gh-pages PHB/visuals/index.html from PHB_visuals_2026-10-23 metrics.  Usage: make_web_page.py <PHB/gallery dir> <PHB/index.html (for the nav)>"""
import json, re, sys, os
from pathlib import Path
DST = Path(sys.argv[1]); CSSSRC = Path(sys.argv[2])
OUT = Path("/scratch/sroy85/Github/dna/large_crystal/PHB_visuals_2026-10-23")
idx = {r["name"]: r for r in json.load(open(OUT / "index.json"))}
A = json.load(open(OUT / "analysis" / "analysis.json"))
NAV = re.search(r'<nav class="site".*?</nav>', CSSSRC.read_text(), re.S).group(0).replace(' class=on', '').replace('<a href="mgl.html"', '<a href="gallery.html" class=on>Gallery &amp; videos</a><a href="mgl.html"', 1) if 'gallery.html' not in CSSSRC.read_text() else re.search(r'<nav class="site".*?</nav>', CSSSRC.read_text(), re.S).group(0).replace(' class=on', '').replace('<a href="gallery.html">', '<a href="gallery.html" class=on>')
EXTRA = """
.vgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin:16px 0}
.vgrid figure{margin:0}.vgrid video{width:100%;border-radius:6px;background:#fff;display:block}
.vc{margin:18px 0}video{max-width:100%}
.sw{display:inline-block;width:.85em;height:.85em;border-radius:50%;border:1px solid #333;vertical-align:-1px;margin-right:4px}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.85em}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:900px){.two{grid-template-columns:1fr}}
figure{margin:14px 0}figure img{width:100%;height:auto;display:block;border-radius:6px;background:#fff}
"""
pc = lambda x: f"{100*x:.1f}%"
def m(n): return idx[n]
def row(n, extra=""):
    f, i = m(n)["final"], m(n)["initial"]
    return f"<tr><td><code>{n}</code></td><td>{m(n)['label']}</td><td>{f['step']:.3g}</td><td>{pc(f['largest_cluster'])}</td><td>{pc(f['six_valent'])}</td><td>{f['mean_valence']:.2f}</td><td>{f['tetra_per_molecule']:.3f}</td>{extra}</tr>"
def table(names):
    return ('<div class="tablewrap"><table><tr><th>Run</th><th>System</th><th>Step</th><th>Largest cluster</th><th>Six-valent</th><th>Valence</th><th>Tetra / mol</th></tr>'
            + "".join(row(n) for n in names) + "</table></div>")
def vid(n, cap=None, turn=False):
    f = f"{n}_turntable" if turn else n
    c = cap or (m(n)["label"] + (" (final state, rotating)" if turn else ""))
    return f'<figure><video controls preload="none" playsinline poster="vid/{f}.jpg" src="vid/{f}.mp4"></video><figcaption>{c} <span class="tag">[{f}]</span></figcaption></figure>'
def iv(n, note=""):
    i, f = m(n)["initial"], m(n)["final"]
    cap = (f"<b>{m(n)['label']}</b> - left: initial (step {i['step']:.3g}; cluster {pc(i['largest_cluster'])}, six-valent {pc(i['six_valent'])}); "
           f"right: final (step {f['step']:.3g}; cluster {pc(f['largest_cluster'])}, six-valent {pc(f['six_valent'])}, valence {f['mean_valence']:.2f}, tetra/mol {f['tetra_per_molecule']:.3f}). {note}")
    return f'<figure><img loading="lazy" src="img/{n}_initial_vs_final.jpg" alt="{m(n)["label"]}: initial and final"><figcaption>{cap}</figcaption></figure>'
def im(fn, cap): return f'<figure><img loading="lazy" src="img/{fn}" alt=""><figcaption>{cap}</figcaption></figure>'
nvid = sum(1 for r in idx.values() if r["video"]); nturn = sum(1 for r in idx.values() if r["turntable"])
ka = {(round(r["Ka"]), r["alpha"]): r for r in A["ka_alpha"]}
kt = "".join(f"<tr><td>{k}</td>" + "".join((f"<td>{pc(ka[(k,a)]['six_08'])} &rarr; {pc(ka[(k,a)]['six_final'])}</td><td>{ka[(k,a)]['tet_final']:.3f}</td>" if (k, a) in ka else "<td>-</td><td>-</td>") for a in (0.10, 0.12)) + "</tr>" for k in (10, 30, 100, 300, 1000))
tt = {(t["variant"], t["T"]): t for t in A["two_species_vs_T"]}
tv = "".join(f"<tr><td>{T}</td><td>{14.3*0.14/T:.1f}</td>" + "".join(f"<td>{pc(tt[(v,T)]['six'])}</td><td>{tt[(v,T)]['valence']:.2f}</td><td>{pc(tt[(v,T)]['cluster'])}</td>" for v in ("3H3L", "5L1H")) + "</tr>" for T in (0.14, 0.15, 0.16, 0.17, 0.18))

H = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gallery: initial and final states, videos, .mgl files | PHB crystal assembly</title><meta name="description" content="Initial and final configurations, helix-bundle renders, videos and cogli .mgl files for the PHB assembly runs (2026-10-23).">
<link rel="stylesheet" href="style.css"><style>{EXTRA}</style></head><body>
<header class="top"><a class="brand" href="index.html">PHB crystal assembly</a><span class="tag">oxDNAcpp</span><span class="sp"></span><a class="oxhome" href="../">oxDNAcpp home</a><button id="th" aria-label="Toggle theme">Theme</button></header>
{NAV}
<div class="wrap"><nav class="toc" id="toc" aria-label="On this page"></nav><main>
<h1>PHB runs: initial and final states, helix-bundle renders, videos and .mgl files</h1>
<p class="lead">Every important run of the campaign, drawn with the helix bundles, with a different colour for each species and a visible distinction between molecules that have joined the growing cluster and those that have not. Companion to the <a href="index.html">overview page</a>. Data as of 2026-10-23.</p>
<div class="kpi"><div><b>{len(idx)}</b><span>runs, each with its initial and final configuration</span></div><div><b>{nvid + nturn}</b><span>videos ({nvid} full trajectories + {nturn} turntables)</span></div><div><b>{2*len(idx)*2}</b><span>.mgl files for cogli (species-coloured and patch-coloured)</span></div><div><b>0.35</b><span>tetrahedra per molecule reached from a 256-molecule seed (ideal 0.358)</span></div></div>

<h2 id="key">1. How to read the pictures</h2>
<div class="card info"><h4>Colour key</h4>
<span class="sw" style="background:#e4572e"></span>species I &nbsp; <span class="sw" style="background:#2e86de"></span>species II &nbsp; <span class="sw" style="background:#2fb344"></span>species III &nbsp; <span class="sw" style="background:#8e44ad"></span>species IV (the 2-species runs only use I and II).
<ul>
<li>A molecule is one large <b>core</b> sphere plus three <b>helix arms</b> of five beads. Arms are drawn <b>lighter</b> than the core.</li>
<li><b>Dark core</b> = the molecule is bonded to six distinct neighbours (the crystal-like environment).</li>
<li><b>Washed, grey-tinted</b> = not in the largest cluster (free molecules, small clusters). A growing cluster therefore stands out from what it has not yet captured.</li>
<li>Bonds are complementary patch colours within 0.3, minimum image: the same detector as the <a href="method.html">method page</a>. Positions are wrapped molecule by molecule so that arms never separate from their cores at the box boundary.</li>
</ul></div>

<h2 id="crystal">2. A crystal you can see: the pre-formed 2048-molecule lattice</h2>
<p>The reference lattice (weak-weak, K<sub>far</sub> = 2) started as three blocks; the main block is 71% of the molecules. It stays intact for 1.7&times;10<sup>9</sup> steps at T = 0.10 (six-valent 61.5% &rarr; 63.8%, tetrahedra per molecule 0.357 &rarr; 0.374), also with very floppy arms (K<sub>b</sub> = 1: 61.7% &rarr; 63.4%). The slabs below are 7-unit cuts through the main block and show the four-species framework: cores of the four species bridged by arm bundles.</p>
<div class="two">{im('crystal_Kb300_T0.100_initial_slabz.jpg','Initial lattice, 7-unit slab viewed along z.')}{im('crystal_Kb300_T0.100_final_slabx.jpg','After 1.7&times;10<sup>9</sup> steps (K<sub>b</sub> = 300), slab viewed along x: the lattice is unchanged.')}</div>
<div class="two">{im('crystal_Kb300_T0.100_final_slabz.jpg','Final, slab along z.')}{im('crystal_Kb1_T0.100_final_slaby.jpg','K<sub>b</sub> = 1 (floppy arms), final, slab along y: the lattice survives.')}</div>
{iv('crystal_Kb300_T0.100','The two smaller blocks stay outside the main cluster (washed).')}
<div class="vc">{vid('crystal_Kb300_T0.100', turn=True)}</div>
<p class="tag">No trajectory video of this run: the stiffness-sweep trajectories contain only 3 frames. The turntable shows the final configuration.</p>

<h2 id="seeding">3. Seeded growth: a crystalline seed captures the gas</h2>
<p>A compact seed of 8 to 256 molecules sits in a gas of pre-attached units (500 molecules, four species, weak-weak, K<sub>far</sub> = 2, T = 0.14). Initial pictures show the seed (colour) in its gas (washed); final pictures show how much of it the cluster has captured and how ordered it is.</p>
{table(['seed_S8_T0.140','seed_S64_T0.140','seed_S128_T0.140_r2','seed_S192_T0.140_r1','seed_S256_T0.140_r1','seed_S256_T0.140_r2','window_Q_T0.140'])}
{iv('seed_S8_T0.140','A small seed still grows to a partial network.')}
{iv('seed_S128_T0.140_r2')}
{iv('seed_S256_T0.140_r1','The largest seed ends closest to the reference crystal (0.345 against 0.358 tetrahedra per molecule).')}
<div class="two">{im('seed_S256_T0.140_r1_final_slabz.jpg','256-molecule seed, final, 10-unit slab along z: arm bundles join cores of different species into a lattice-like network.')}{im('seed_S128_T0.140_r2_final_slabz.jpg','128-molecule seed, final, slab along z.')}</div>
<div class="vgrid">{vid('seed_S256_T0.140_r1')}{vid('seed_S256_T0.140_r1', turn=True)}{vid('seed_S128_T0.140_r2')}{vid('seed_S128_T0.140_r2', turn=True)}{vid('seed_S64_T0.140')}{vid('seed_S8_T0.140')}{vid('window_Q_T0.140','No seed: melt at T = 0.17, then hold at T = 0.14.')}{vid('seed_S192_T0.140_r1')}{vid('seed_S256_T0.140_r2')}</div>
<h3>Too hot: the seed melts</h3>
{table(['seed_S32_T0.150','seed_S128_T0.150','seed_S8_T0.160','seed_S128_T0.160'])}
<div class="vgrid">{vid('seed_S128_T0.150')}{vid('seed_S128_T0.160')}{vid('seed_S8_T0.160')}{vid('seed_S32_T0.150')}</div>
<p>At T = 0.15 small seeds melt and a 128-molecule seed is only partly kept; at T = 0.16 every seed dissolves (largest cluster 2%). The usable window is narrow and sits just below the melting point.</p>

<h2 id="ka">4. Does the angular stiffness K<sub>a</sub> or the patch width &alpha; matter for crystallisation?</h2>
<p>The same 128-molecule seed system (T = 0.14, same start configuration) run for 2&times;10<sup>9</sup> steps with K<sub>a</sub> in {{10, 30, 100, 300, 1000}} and &alpha; = 0.10 and 0.12. {sum(1 for r in A['ka_alpha'])} runs.</p>
{im('ka_alpha.jpg','Left and middle: six-valent fraction against time (dashed: the K<sub>a</sub> = 300, &alpha; = 0.10 control, 0.8&times;10<sup>9</sup> steps). Right: tetrahedra per molecule at the end.')}
<div class="tablewrap"><table><tr><th rowspan="2">K<sub>a</sub></th><th colspan="2">&alpha; = 0.10</th><th colspan="2">&alpha; = 0.12</th></tr><tr><th>six-valent at 0.8&times;10<sup>9</sup> &rarr; 2&times;10<sup>9</sup></th><th>tetra / mol</th><th>six-valent at 0.8&times;10<sup>9</sup> &rarr; 2&times;10<sup>9</sup></th><th>tetra / mol</th></tr>{kt}</table></div>
<div class="card good"><h4>What it shows</h4>
<ul>
<li><b>Crystallisation from a seed occurs at every K<sub>a</sub> from 10 to 1000 and at both &alpha;</b>: all runs grow from 10% to 32&ndash;42% six-valent molecules and reach 0.28&ndash;0.32 tetrahedra per molecule, and are still rising at 2&times;10<sup>9</sup> steps (about +10 points per 10<sup>9</sup> steps at &alpha; = 0.10).</li>
<li><b>K<sub>a</sub> has no measurable effect at &alpha; = 0.10</b>; time-matched at 0.8&times;10<sup>9</sup> steps all values sit at 27&ndash;30% against 30% for the control.</li>
<li><b>&alpha; = 0.10 ends better than 0.12</b> (mean 0.316 against 0.289 tetrahedra per molecule; replicate scatter of this system is about 0.01). At &alpha; = 0.12 the two stiffest values (K<sub>a</sub> = 300, 1000) flatten near 31% while K<sub>a</sub> &le; 100 reach 37&ndash;39%; this needs replicates before it is called an effect.</li>
</ul></div>
<div class="vgrid">{''.join(vid(n) for n in ['Ka10_a0.10','Ka30_a0.10','Ka100_a0.10','Ka1000_a0.10','Ka10_a0.12','Ka30_a0.12','Ka100_a0.12','Ka300_a0.12','Ka1000_a0.12'])}</div>
<p class="tag">The K<sub>a</sub> = 1000, &alpha; = 0.12 run was still running (step 1.86&times;10<sup>9</sup>) when rendered.</p>

<h2 id="two">5. Two species</h2>
<p>Each molecule carries three handles and three receptors; the six channels are strong (K = 200) or weak (K = 2) per design. At T = 0.14, K<sub>weak</sub>/T = 14.3 lies in the reversibility window. All four designs end as gels; the designs with more weak channels have more six-valent molecules.</p>
{table(['2sp_equal_T0.140','2sp_5H1L_T0.140','2sp_3H3L_T0.140','2sp_5L1H_T0.140'])}
<div class="vgrid">{vid('2sp_equal_T0.140')}{vid('2sp_5H1L_T0.140')}{vid('2sp_3H3L_T0.140')}{vid('2sp_5L1H_T0.140')}{vid('2sp_3H3L_T0.140', turn=True)}{vid('2sp_5L1H_T0.140', turn=True)}</div>
{iv('2sp_3H3L_T0.140','A gel: one connected cluster, mostly four-valent.')}
{iv('2sp_5L1H_T0.140')}
<h3>Does a higher temperature help?</h3>
<p>The two best designs were run from the same 32-molecule seed at T = 0.15 to 0.18 for 2&times;10<sup>9</sup> steps. <b>No.</b> Order falls steadily above T = 0.14, and the design with five weak channels melts into separate clusters at T &ge; 0.17.</p>
{im('two_species_vs_T.jpg','Final six-valent fraction, largest cluster and mean valence against temperature.')}
<div class="tablewrap"><table><tr><th rowspan="2">T</th><th rowspan="2">K<sub>weak</sub>/T</th><th colspan="3">3-3 (3H3L)</th><th colspan="3">1-5 (5L1H)</th></tr><tr><th>six-valent</th><th>valence</th><th>cluster</th><th>six-valent</th><th>valence</th><th>cluster</th></tr>{tv}</table></div>
<div class="vgrid">{''.join(vid(f'2sp_highT_{v}_T{T}') for v in ('3H3L','5L1H') for T in ('0.150','0.160','0.170','0.180'))}</div>
<div class="card warn"><h4>Reading</h4>For K<sub>weak</sub> = 2 the sensitive zone for the two-species system is at or just below T = 0.14 (K/T 13&ndash;14), not above. Untested: T between 0.14 and 0.15, and weaker bonds with larger seeds, which are the obvious next runs.</div>

<h2 id="four">6. Four species, 32-molecule seed</h2>
{table(['4sp_ww_T0.140','4sp_ws_T0.140','4sp_ww_T0.078','4sp_seed8_ws_T0.140'])}
<p>Weak-weak (K = 2) at T = 0.14 reaches 44% six-valent molecules and 0.28 tetrahedra per molecule (partly ordered). The same system at T = 0.078 (K/T = 26) and the weak-strong system (K &asymp; 101) at T = 0.14 stay gels (9&ndash;10% six-valent): bonds that cannot break cannot anneal.</p>
{iv('4sp_ww_T0.140')}{iv('4sp_ws_T0.140','This run was still going when rendered.')}
<div class="vgrid">{vid('4sp_ww_T0.140')}{vid('4sp_ww_T0.140', turn=True)}{vid('4sp_ws_T0.140')}{vid('4sp_ww_T0.078')}{vid('4sp_seed8_ws_T0.140')}</div>

<h2 id="timecourse">7. Time courses</h2>
{im('timecourses_headline.jpg','Six-valent fraction and largest-cluster fraction against step for the headline runs.')}

<h2 id="dl">8. Files</h2>
<ul>
<li><a href="dl/PHB_mgl_species_all_runs.zip">PHB_mgl_species_all_runs.zip</a> (11 MB): initial and final <code>.mgl</code> of all {len(idx)} runs, species-coloured, wrapped.</li>
<li><a href="dl/PHB_mgl_patches_headline_runs.zip">PHB_mgl_patches_headline_runs.zip</a> (7 MB): initial and final <code>.mgl</code> with patches drawn, for the headline runs; made with oxDNAcpp <code>terminal autoconvert</code>, positions wrapped into the box.</li>
<li>Videos on this page are 854&times;480 re-encodings. Full-resolution (1280&times;720) originals, all configurations, topologies, <code>index.json</code> and a README are in <code>large_crystal/PHB_visuals_2026-10-23/</code> on the cluster.</li>
</ul>
<pre><code>cogli2 PHB_seed_S256_T0.140_r1_final_species.mgl   # after unzipping</code></pre>
<p>Naming: <code>&lt;run&gt;_initial|final_species.mgl</code> / <code>_patches.mgl</code>. File names of runs: <code>2sp_*</code> two species, <code>4sp_*</code> four species with a 32-molecule seed, <code>seed_S&lt;n&gt;_T&lt;T&gt;</code> seeded growth, <code>Ka&lt;K&gt;_a&lt;alpha&gt;</code> the K<sub>a</sub> study, <code>2sp_highT_*</code> two species at T &ge; 0.15, <code>crystal_*</code> the pre-formed lattice.</p>

<h2 id="limits">9. Caveats</h2>
<ul>
<li>Initial configurations are the structures the MD started from (after a short MC relaxation); the two-species and four-species 32-seed starts contain pre-attached arms but no inter-molecular bonds by construction.</li>
<li>Videos show 150 frames sampled evenly from the first to the last <i>complete</i> trajectory frame. Runs that were still running when rendered end at that moment.</li>
<li>These are structure-only (topological) measures. Long-range order, structure factors and defect statistics are not yet quantified; single runs per setting except where stated.</li>
</ul>
<p class="tag">Generated from the project data on 2026-10-23.</p>
</main></div>
<div id="lb" hidden><img alt=""><p></p></div>
<script src="site.js"></script></body></html>"""
import re as _re
rows = []
for r in idx.values():
    for kind, key in (("trajectory", "video"), ("turntable", "turntable")):
        if r[key]:
            fn = Path(r[key]).name; sz = (DST / "vid" / fn).stat().st_size / 1e6
            rows.append(f'<tr><td><a href="vid/{fn}">{fn}</a></td><td>{r["label"]}</td><td>{kind}</td><td>{sz:.1f} MB</td></tr>')
ALLV = '<h2 id="allvideos">9. Every video</h2><p>All ' + str(len(rows)) + ' videos are hosted on this site (854&times;480, H.264, about 2 MB each, ' + f"{sum(float(x.split('MB')[0].split('>')[-1]) for x in rows):.0f}" + ' MB in total); the table links each file directly. Trajectory videos show 150 frames from the first to the last complete frame; turntables rotate the final configuration.</p><div class="tablewrap"><table><tr><th>File</th><th>Run</th><th>Type</th><th>Size</th></tr>' + "".join(sorted(rows)) + '</table></div>'
H = H.replace('<h2 id="limits">9. Caveats</h2>', ALLV + '<h2 id="limits">10. Caveats</h2>')
H = _re.sub(r'(src|poster|href)="(img|vid|dl)/', r'\1="gallery/\2/', H)
H = H.replace('<img loading="lazy"', '<img class="zoom" loading="lazy"')
(DST.parent / "gallery.html").write_text(H)
# sanity: every referenced local asset exists
refs = set(re.findall(r'(?:src|poster|href)="(gallery/(?:img|vid|dl)/[^"]+)"', H))
miss = [r for r in refs if not (DST.parent / r).exists()]
print("page bytes", len(H), "refs", len(refs), "missing", miss)
