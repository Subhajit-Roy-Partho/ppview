#!/usr/bin/env python3
"""Generate oxDNAcpp gh-pages PHB/summary.html (synthesis). Usage: make_summary_page.py <PHB dir>"""
import re, sys
from pathlib import Path
P = Path(sys.argv[1])
SRC = {  # tag -> (label, href or None)
 "S1": ("archive page", "archive.html"), "S2": ("hand5 page", "hand5.html"), "S3": ("seeding page", "seeding.html"),
 "S4": ("window-scan page", "window-scan.html"), "S5": ("method page", "method.html"), "S6": ("corrections page", "corrections.html"),
 "S7": ("about page", "about.html"), "S8": ("gallery page (new runs)", "gallery.html"),
 "D1": ("PHB_complete_analysis_2026-10-09.md", None), "D2": ("PHB_archive_findings.md", None), "D3": ("PHB_paper_roadmap.md", None),
 "D4": ("PHB_literature_review.md", None), "D5": ("PHB.tex", None),
 "N1": ("findings/two_species.md", None), "N2": ("findings/param_run.md", None), "N3": ("findings/param_ka.md", None), "N4": ("PHB_visuals_2026-10-23/analysis", None),
}
def c(tag, where=""):
    lab = f"{tag}" + (f" {where}" if where else "")
    href = SRC[tag][1]
    if href: lab_html = f'<a href="{href}">{lab}</a>'
    else: lab_html = f'<a href="#src-{tag}">{lab}</a>'
    return f'<span class="cite">[{lab_html}]</span>'
def ci(*a): return c(*a).replace('class="cite"','class="cite" style="display:inline"')
def pill(t, k): return f'<span class="pill p-{k}">{t}</span>'
H = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Summary: what controls PHB crystallisation | PHB crystal assembly</title><meta name="description" content="Synthesis of the archive, hand5 and new runs: results, which parameters control crystallisation, whether heterogeneous bond strengths help, what is unexplained, and what to run next. Every claim is tagged with its source.">
<link rel="stylesheet" href="style.css"><style>.cite{{font-size:.76rem;color:var(--mute);white-space:nowrap}}.cite a{{color:var(--mute)}}td .cite{{display:block;white-space:normal}}.p-rb{{color:var(--good)}}.p-sr{{color:var(--warn)}}.p-hy{{color:var(--accent2)}}.p-no{{color:var(--mute)}}</style></head><body>
<header class="top"><a class="brand" href="index.html">PHB crystal assembly</a><span class="tag">oxDNAcpp</span><span class="sp"></span><a class="oxhome" href="../">oxDNAcpp home</a><button id="th" aria-label="Toggle theme">Theme</button></header>
@@NAV@@
<div class="wrap"><nav class="toc" id="toc" aria-label="On this page"></nav><main>
<h1>Summary: what controls crystallisation of patchy helix bundles</h1>
<p class="lead">A synthesis of the whole campaign: the 2024&ndash;2026 archive, the hand5 sweeps, the seeding series and window scan, and the runs added on 2026-10-23. It lists the results, the parameters that matter and those that do not, whether heterogeneous bond strengths help, what looks interesting, and what to run next. Every statement carries a source tag; the key is in <a href="#sources">section 7</a>. Confidence is marked: {pill('robust','rb')} several independent runs or datasets, {pill('single run','sr')} n = 1 per setting, {pill('hypothesis','hy')} consistent with the data but not directly tested.</p>

<div class="card info"><h4>Bottom line</h4><ol>
<li><b>Crystals did form, but only in a narrow window of reduced bond strength, K/T &asymp; 12&ndash;14, just below melting.</b> Best cases: 486 of 500 cores in one crystallite (archive, T<sub>eff</sub> = 0.075), 0.332 tetrahedra per molecule (best archive run; ideal crystal 0.358), and 0.345 from a 256-molecule seed at T = 0.14. {c('S1','K/T table')} {c('S3')} {pill('robust','rb')}</li>
<li><b>Everything outside the window is an arrested network:</b> it connects fast (about 3&times;10<sup>8</sup> steps; 72 of 72 seeded-sweep runs), but ends with valence about 4 and 0.07&ndash;0.13 tetrahedra per molecule for K/T &ge; 20, whatever the bond depth. Strong bonds do not help; they stabilise the traps. {c('S2')} {c('D1','findings 1&ndash;2')} {c('D4','Hagan et al.')} {pill('robust','rb')}</li>
<li><b>A crystalline seed removes the bottleneck; an unseeded quench does not.</b> At T = 0.14, seeds of 128, 192 and 256 molecules ended ordered in all 7 placement runs; the best unseeded quench reaches only 0.18. {c('S3')} {c('S4')} {pill('robust','rb')}</li>
<li><b>Decisive parameters:</b> K/T (bond reversibility), temperature within the window, and seeding. <b>Weak or no effect:</b> K<sub>a</sub>, K<sub>b</sub>, bond-strength distribution. <b>Modest:</b> patch width &alpha; (0.10 beats 0.12; narrow 0.03 fails in the archive), arm length. {c('S8','Ka x alpha')} {c('S1')} {c('N2')}</li>
<li><b>Heterogeneous strengths do not help by themselves.</b> They help only to the extent that they make some channels reversible; at equal reversibility no benefit has been shown, and the decisive annealing-regime test has not been run. {c('S1','strength variants')} {c('S2','decisive equal-K')} {c('N1')} {c('D3','B7')}</li>
<li><b>Not shown:</b> long-range order (no structure factor or orientational order parameters yet), unseeded nucleation, a direct melting line, replicates for most points, and any mapping to experiment. {c('S7')} {c('D3','A&ndash;C')}</li></ol></div>

<h2 id="results">1. Results by dataset</h2>
<div class="tablewrap"><table>
<tr><th>Dataset</th><th>System</th><th>Outcome</th><th>Key numbers</th><th>Source</th></tr>
<tr><td>Archive (2024&ndash;Mar 2026)</td><td>500 molecules, K<sub>far</sub> = 1 (and 10 from pre-formed seeds); 1,039 endpoints</td><td>Crystals form from a dispersed or lattice start in a window; sharp melting step</td><td>101 endpoints with &ge; 50 % of cores in one crystallite; 37 with &ge; 0.20 tetra/mol; melts 0.082 &rarr; 0.083 (315 &rarr; 13 cores, K/T 12.2 &rarr; 12.0)</td><td>{c('S1')}</td></tr>
<tr><td>hand5 sweeps (stiffness, seeded, pre-connected, strength, equal-K)</td><td>500 molecules (2048 for stiffness), K = 2 or 100&ndash;400, T = 0.05&ndash;0.20</td><td>Always connected, arrested</td><td>valence 3.9&ndash;4.3, 0.07&ndash;0.13 tetra/mol; exception ww, T = 0.14: 40 % six-valent</td><td>{c('S2')} {c('D1')}</td></tr>
<tr><td>Window scan</td><td>ww, K = 2, melt at T = 0.17, then hold or ramp</td><td>Unseeded: aggregates at T = 0.12, partial order at 0.14 (0.18), nothing at &ge; 0.15; ordered state melts near 0.165</td><td>0.114 / 0.146 / 0.180 tetra/mol at T = 0.12 / 0.13 / 0.14</td><td>{c('S4')}</td></tr>
<tr><td>Seeding series</td><td>seeds of 8&ndash;256 molecules, ww, T = 0.14</td><td>Seed grows; order rises with seed size; dissolves at T = 0.16</td><td>0.184 (8), 0.212 (64), 0.25 (128), 0.29 (192), 0.345 (256) tetra/mol</td><td>{c('S3')}</td></tr>
<tr><td>Pre-formed 2048-molecule lattice</td><td>K = 2, K<sub>b</sub> = 1&ndash;300, T = 0.05&ndash;0.10</td><td>Stable in all 72 conditions</td><td>0.372 tetra/mol in all; 0.357 &rarr; 0.374 over 1.7&times;10<sup>9</sup> steps (K<sub>b</sub> = 300)</td><td>{c('S2')} {c('S8','crystal')}</td></tr>
<tr><td>New: K<sub>a</sub> &times; &alpha;</td><td>128-seed, ww, T = 0.14, K<sub>a</sub> 10&ndash;1000, &alpha; 0.10 / 0.12, 2&times;10<sup>9</sup> steps</td><td>Seeded growth in every run, still rising</td><td>0.28&ndash;0.32 tetra/mol; &alpha; = 0.10 mean 0.316 vs 0.289 at 0.12</td><td>{c('S8','section 4')} {c('N4')}</td></tr>
<tr><td>New: two species, T = 0.14&ndash;0.18</td><td>equal, 5-1, 3-3, 1-5 strength designs; 32-seed</td><td>All gels; order falls above T = 0.14</td><td>six-valent at T = 0.14: 6.2 / 10.0 / 13.0 / 15.6 %</td><td>{c('S8','section 5')} {c('N1')}</td></tr>
<tr><td>New: four species, 32-seed</td><td>ww (K = 2) vs ws (K &asymp; 101), T = 0.14</td><td>ww partly ordered, ws gel</td><td>ww six-valent 40 % ({ci('S2')}) &rarr; 44 % at 1.5&times;10<sup>9</sup> steps; ws 9 %</td><td>{c('S8','section 6')}</td></tr>
</table></div>

<h2 id="params">2. Which parameters affect crystallisation</h2>
<div class="tablewrap"><table>
<tr><th>Parameter</th><th>Effect</th><th>Evidence</th><th>Confidence</th></tr>
<tr><td><b>Reduced bond strength K/T</b></td><td><b>Decisive.</b> Ordered at K/T 12&ndash;14; partly trapped 15&ndash;20; arrested 20&ndash;4000; melted below about 11.5.</td><td>Archive K = 1 (T<sub>eff</sub> 0.073&ndash;0.083) and hand5 K = 2 (T = 0.14) fall on the same window and melt at the same K/T &asymp; 12. New: the 1-5 two-species design (K<sub>weak</sub> = 2) breaks into 10&ndash;14 clusters at T &ge; 0.17 (K/T = 11.8), matching the predicted T<sub>m</sub> = 2/12 = 0.167. {c('S1','order vs reversibility')} {c('S4')} {c('S8','section 5')} {c('D3','B1')}</td><td>{pill('robust','rb')} window; {pill('hypothesis','hy')} as a phase boundary (no direct melting line)</td></tr>
<tr><td>Bond depth K at fixed K/T</td><td>Only K/T matters; K = 1 and 10 work in the archive (K = 10 only from pre-formed seeds); K &ge; 11 gave no crystal in 198 runs, nor K &le; 0.2 or = 2 in that archive.</td><td>{c('S1','K<sub>far</sub> table')} {c('D2','4.1')}. Equal-K controls: 299+1, 150+150, 1+299 and 1+1 trap identically. {c('S2','decisive_equalK')} {c('D1','D3')}</td><td>{pill('robust','rb')}</td></tr>
<tr><td>Temperature</td><td>Optimum just below melting (T = 0.14 for K = 2). Hotter melts seeds (T = 0.15 small seeds, 0.16 all); colder gives aggregates. Assembly time falls with T.</td><td>{c('S3')} {c('S4')} {c('S2','t<sub>95</sub> vs T')}. New: two species get worse at 0.15&ndash;0.18 (3-3 six-valent 13 &rarr; 10 &rarr; 7 &rarr; 4 &rarr; 3 %). {c('S8','section 5')}</td><td>{pill('robust','rb')}</td></tr>
<tr><td>Seeding and seed size</td><td><b>Decisive for order in hand5.</b> Order rises with seed size; unseeded quench stays partial.</td><td>{c('S3')} {c('S4')}. The critical nucleus for partial order is below 8 molecules; the earlier &ldquo;about 128&rdquo; was a monitor bug. {c('S6','E9')}</td><td>{pill('robust','rb')} (&ge; 128: 7 of 7); small seeds single runs</td></tr>
<tr><td>Patch width &alpha;</td><td>Narrow fails, 0.10 beats 0.12.</td><td>Archive PHB4: raising &alpha; from 0.03 to 0.10 takes the best run from 38 to 650 spacers (3 to 386 cores). New: &alpha; = 0.10 ends at 0.316 vs 0.289 tetra/mol (0.12), scatter about 0.01. {c('D2','4.2')} {c('S8','section 4')}. Caveat: only 0.03 vs 0.10 is valid in the archive (mislabelled ladders). {c('S6','D8')}</td><td>{pill('single run','sr')} each</td></tr>
<tr><td>Angular stiffness K<sub>a</sub></td><td>No measurable effect at &alpha; = 0.10 (27&ndash;30 % six-valent at 0.8&times;10<sup>9</sup> steps for K<sub>a</sub> 10&ndash;1000 vs 30 % control). At &alpha; = 0.12 the stiffest values (300, 1000) plateau near 31 % vs 37&ndash;39 % for &le; 100: a hint.</td><td>{c('S8','section 4')} {c('N4')}. The old 31-bead K<sub>a</sub> 100 vs 300 sweep cannot answer the question: its final states are a restart artefact. {c('N3')}</td><td>{pill('single run','sr')}</td></tr>
<tr><td>Arm bending stiffness K<sub>b</sub></td><td>None for the pre-formed lattice (72 runs, K<sub>b</sub> down to 1). In dilute assembly a modest effect on network quality (K<sub>b</sub> = 1 vs 300: 0.109 vs 0.083 tetra/mol), none on assembly time.</td><td>{c('S2')} {c('N2','section 2')}. The dissertation notes call K<sub>b</sub> irrelevant ({ci('D1','&sect;parameters')}); the newer analysis finds the small dilute effect, see <a href="#disagree">section 6</a>.</td><td>{pill('robust','rb')} none on lattice; {pill('single run','sr')} dilute effect</td></tr>
<tr><td>Arm length</td><td>10-bead arms give the best self-assembled crystals from a lattice start (499&ndash;500 cores, 15,500 particles); 7-bead seeded runs grow (466 cores); 10-bead seeded runs fragment (transport-limited). hand5 used 5 beads only.</td><td>{c('D2','4.1')} {c('S1','coverage')}</td><td>{pill('single run','sr')}</td></tr>
<tr><td>Thermal protocol</td><td>Holding at T = 0.14 beats ramps; slow cooling did not remove disorder; melt&ndash;re-freeze is reversible for K = 2, impossible for K &asymp; 101.</td><td>{c('S4')} {c('S2','kick experiment')}</td><td>{pill('single run','sr')}</td></tr>
<tr><td>Run length</td><td>Short runs masquerade as melting (PHB4 was 10&times; shorter than PHB5); seeded curves are still rising at 2&times;10<sup>9</sup> steps.</td><td>{c('S1','PHB4')} {c('S8','section 4')}</td><td>{pill('robust','rb')}</td></tr>
<tr><td>Number of species</td><td>Two species: gel at every setting tried (best 15.6 % six-valent). Four species with a seed: partly ordered (44 %). Two species halves the design effort but has no crystal geometry to cut a seed from.</td><td>{c('S8','sections 5&ndash;6')} {c('N1')} {c('D1','&sect;two-species')}</td><td>{pill('single run','sr')}</td></tr>
<tr><td>Starting state</td><td>Order from pre-formed seeds is inherited, not annealed (PHB3, K = 10, K/T 50&ndash;500). Lattice starts (PHB4/5), seeded gas (hand5) are not comparable.</td><td>{c('S1','caveat 2')}</td><td>{pill('robust','rb')}</td></tr>
<tr><td>Simulated Hamiltonian</td><td>The archive topologies carry a trailing-space quirk that duplicates one patch per group; hand5 does not. A control run is pending.</td><td>{c('S1','caveat 1')} {c('D3','A2')}</td><td>{pill('no data','no')}</td></tr>
</table></div>

<h2 id="hetero">3. Do heterogeneous bond strengths help crystallisation?</h2>
<p>&ldquo;Heterogeneous&rdquo; can mean three things in this project, and the answers differ.</p>
<div class="tablewrap"><table>
<tr><th>Meaning</th><th>Result</th><th>Source</th></tr>
<tr><td>Uneven strengths across the patch classes at the same overall reversibility (archive PHB5: <code>square</code> and <code>weakSquare</code> vs symmetric weak <code>equal</code>)</td><td>All three give crystals. Final energy differs by variant (about &minus;88, &minus;44, 0) while order varies freely within each. Tetrahedra per molecule at T<sub>eff</sub> 0.075&ndash;0.077: square 0.27&ndash;0.29, weakSquare 0.27&ndash;0.28, equal 0.25&ndash;0.26 (single runs; slightly lower for equal). &ldquo;The lattice is correct geometrically even when it is barely bound.&rdquo;</td><td>{c('S1','energy bookkeeping, table')} {c('D2','4.1&ndash;4.2')}</td></tr>
<tr><td>Strong core patch and weak far-tip (hand5 ws, K = 101) vs symmetric weak (ww, K = 2); equal-K controls (299+1, 150+150, 1+299 vs 1+1); strength scan K = 100&ndash;400</td><td>Depth, not distribution, decides: ww orders at T = 0.14, ws never does; the equal-K variants are indistinguishable (valence 3.85&ndash;4.12, 0.06&ndash;0.09 tetra/mol) and so are all strengths 100&ndash;400. All of these were run where nothing can anneal, so they cannot show an advantage.</td><td>{c('S2')} {c('D1','D3')}</td></tr>
<tr><td>Channel-by-channel strength in the two-species designs (new)</td><td>At T = 0.14 the six-valent fraction rises with the number of weak (reversible) channels: 0 weak 6.2 %, 1 weak 10.0 %, 3 weak 13.0 %, 5 weak 15.6 %. 3-3 and 1-5 are a statistical tie. At T &le; 0.11 (K/T &ge; 18) the designs span only about 3 points. All remain gels, and higher T makes them worse.</td><td>{c('S8','section 5')} {c('N1')}</td></tr>
<tr><td>Structural hierarchy (strong anchors holding arms on cores, weak lattice contacts)</td><td>Built into every working run, and necessary: without strong anchors arms float free (this is what broke the first two-species sweep). The weak lattice contact must be reversible; the anchor must not be.</td><td>{c('S5','patches')} {c('D1','finding 3')}</td></tr></table></div>
<div class="card warn"><h4>Verdict</h4><b>Heterogeneity helps only through reversibility.</b> Making some channels weak helps relative to all-strong (6 % &rarr; 14&ndash;16 % six-valent at T = 0.14), but the same effect is obtained by a uniform weak bond at the right K/T, and no run shows a benefit from uneven strengths at equal reversibility. The question that motivated heterogeneity (a strong subunit and a weak lattice bond giving two-stage, error-correcting assembly) can only be answered in the annealing regime, where it has not been tried: the planned test is K = 2 with (1+1), (2+0), (0+2) and K = 4 (2+2) at K/T &asymp; 13.5. {c('D3','B7')} {pill('open','hy')}</div>

<h2 id="interesting">4. What looks interesting</h2>
<ul>
<li><b>Two different Hamiltonians melt at the same K/T &asymp; 12</b> (archive K = 1: T<sub>eff</sub> 0.0825; hand5 K = 2: between 0.16 and 0.17), and a third system, the new two-species 1-5 design with K<sub>weak</sub> = 2, breaks up at T &ge; 0.17. This is the strongest hint that K/T is the right control variable. {c('S1')} {c('S4')} {c('S8')} {pill('hypothesis','hy')}</li>
<li><b>Energy is not a crystal indicator.</b> The lowest-energy runs are disordered aggregates (T = 0.12); the energy of an ordered 482-core state differs from the start by 1 %; failed two-species gels reached &minus;5 to &minus;29 per particle. {c('S5','why energy is not evidence')} {c('S4')}</li>
<li><b>The lattice forms even when barely bound</b> (PHB5 <code>equal</code>, E &asymp; &minus;0.8 per particle): geometry, not binding energy, selects the structure. {c('D2','4.1')}</li>
<li><b>Assembly is fast and encounter-limited:</b> every network of 500 molecules connects in about 3&times;10<sup>8</sup> steps, independent of K<sub>b</sub>, with a universal count of about 95 crystallites at 4&times;10<sup>7</sup> steps. The slow part is annealing, not aggregation. {c('S2','growth mechanism')}</li>
<li><b>Soft arms do not matter for the lattice.</b> The pre-formed crystal survives K<sub>b</sub> = 1 (arm joint angle 22&deg; vs 2&deg;) for 1.2&times;10<sup>9</sup> steps; the floppy limit below K<sub>b</sub> = 1 is not bracketed. {c('N2')} {c('S8','crystal')}</li>
<li><b>Replicate scatter is huge:</b> 7 vs 395 cores at identical &alpha; and T. A single trajectory is not a yield. {c('S1')} {c('S6','D8')}</li>
<li><b>Several apparent results were analysis artefacts</b> (periodic boundaries, a trailing-space topology quirk, a colour-encoding rule for |colour| &lt; 10, truncated files, a restart-splice in the old K<sub>a</sub> sweep, a monitor that used one topology for every seed run). Reading anything older than 2026-10-23 needs the corrections log. {c('S6')} {c('N3')}</li>
<li><b>Literature agrees with the phenomenology</b> (narrow window below melting, strong bonds trap, seeding helps) but not yet quantitatively. {c('D4','&sect;2')} {c('S7')}</li></ul>

<h2 id="next">5. What else could be looked at</h2>
<div class="tablewrap"><table>
<tr><th>Priority</th><th>Experiment</th><th>Question and prediction</th><th>Source</th></tr>
<tr><td>1</td><td>Direct melting line: ramp up and down from an ordered state for K &isin; {{1, 2, 4, 8}}</td><td>T<sub>m</sub> &prop; K with K/T<sub>m</sub> &asymp; 12 (K = 2: 0.167). A prediction that can fail; also gives hysteresis and latent heat.</td><td>{c('D3','B1')}</td></tr>
<tr><td>2</td><td>Heterogeneity in the annealing regime: K = 2 as (1+1), (2+0), (0+2); K = 4 (2+2) at K/T &asymp; 13.5</td><td>Does an uneven split help error correction at equal reversibility? Currently untested.</td><td>{c('D3','B7')}</td></tr>
<tr><td>3</td><td>Two-species at T between 0.14 and 0.15, and with weaker bonds and larger seeds</td><td>The new data show the window is at or below 0.14 for K<sub>weak</sub> = 2; the fine structure is unmapped.</td><td>{c('S8','section 5')}</td></tr>
<tr><td>4</td><td>Longer seeded runs (10<sup>9</sup>&ndash;10<sup>10</sup> steps) and replicates (n &ge; 4) of the K<sub>a</sub> &times; &alpha; runs, plus &alpha; = 0.08, 0.11, 0.15</td><td>Curves are still rising; is the &alpha; = 0.12 plateau at K<sub>a</sub> &ge; 300 real? Where is the optimum &alpha;?</td><td>{c('S8','section 4')} {c('D3','A3')}</td></tr>
<tr><td>5</td><td>Archive control without the trailing-space quirk (PHB5/square, T = 0.076, 0.080; 7-bead seeded)</td><td>Decides whether the archive and hand5 results can be quoted together.</td><td>{c('D3','A2')} {c('S1','caveat 1')}</td></tr>
<tr><td>6</td><td>Structure factor, Steinhardt order parameters, defect census, grain map</td><td>Prove or refute &ldquo;pyrochlore&rdquo;; show where order is lost (grains vs vacancies). No new runs needed.</td><td>{c('D3','B3, B4')} {c('S7','limitations')}</td></tr>
<tr><td>7</td><td>Annealing protocols: slow cooling near T<sub>m</sub>, thermal cycling, isothermal holds from arrested states</td><td>How slow must cooling be? Are arrested states kinetic or a thermodynamic basin?</td><td>{c('D3','B5')} {c('D4','Pine, Hagan')}</td></tr>
<tr><td>8</td><td>Unseeded nucleation, concentration and box size; seeding method for the critical nucleus</td><td>Is a seed needed? Where is n* (below 8 molecules at T = 0.14)? Is the 40<sup>3</sup> box incommensurate with the cell?</td><td>{c('D3','B6, A4')} {c('D4','Espinosa et al.')}</td></tr>
<tr><td>9</td><td>Bond free-energy profile vs &alpha;, K, T</td><td>Explains why the window sits at K/T 12&ndash;14 and predicts how it moves with &alpha; and arm length.</td><td>{c('D3','B2')}</td></tr>
<tr><td>10</td><td>A two-species crystal design (SAT-assembly) from which to cut a seed; arm length and arm-count variations</td><td>Two species is cheaper but has no target geometry here; 10-bead arms were best from lattice starts but fail seeded.</td><td>{c('D4','Rovigatti, Russo')} {c('D2','4.1')}</td></tr>
<tr><td>11</td><td>Unit mapping and optics</td><td>Turn K/T &asymp; 13 into a sticky-end length and anneal temperature; ask whether a 0.2&ndash;0.3 tetra/mol network still has a stop band.</td><td>{c('D3','C1&ndash;C3')}</td></tr></table></div>
<p class="tag">In progress on the cluster (2026-10-23): the incomplete stiffness-sweep, equal-K, pre-connected and low-T seeded runs were resubmitted in chained jobs; they will extend, not change, the conclusions above. {c('N4','ops log')}</p>

<h2 id="disagree">6. Where the sources disagree or limit the conclusions</h2>
<div class="tablewrap"><table>
<tr><th>Topic</th><th>Statement A</th><th>Statement B</th><th>How to read it</th></tr>
<tr><td>K<sub>b</sub></td><td>Irrelevant for assembly and quality {c('D1','&sect;parameters')}</td><td>Modest effect on dilute network quality (p = 0.031 over six T pairs), none on lattice {c('N2')}</td><td>Both agree on the lattice and on assembly time; the dilute effect is small and not replicated.</td></tr>
<tr><td>Critical nucleus</td><td>&ldquo;About 128 molecules, intermittent order&rdquo; (status reports 2026-10-10 to 23)</td><td>Retracted: a monitor used one topology for all runs; every seed &ge; 8 grows at T = 0.14 {c('S3')} {c('S6','E9')}</td><td>Use the seeding page; n* is below 8 molecules and unresolved.</td></tr>
<tr><td>Smooth melting curve</td><td>PHB4 gives melting from 95 % to 1 % between T = 0.066 and 0.120 {c('D5')}</td><td>PHB4 is 10&times; shorter than PHB5; the real step is sharp at T<sub>eff</sub> = 0.082 &rarr; 0.083 {c('S1')} {c('S6','D7')}</td><td>Do not quote the smooth curve.</td></tr>
<tr><td>&alpha; ladders</td><td>&alpha; = 0.03, 0.05, 0.07, 0.10 all compared {c('D5')}</td><td>a03/a05/a07 inputs are identical (&alpha; = 0.03) {c('S6','D8')}</td><td>Only 0.03 vs 0.10 (archive) and 0.10 vs 0.12 (new) are valid.</td></tr>
<tr><td>Seeded growth</td><td>&ldquo;Diffusion-limited, 1.6&ndash;2.8 % cluster&rdquo; {c('D5')}</td><td>Periodic-boundary bug; all runs connect {c('S6','D1')}</td><td>Everything connects; the problem is arrest.</td></tr>
<tr><td>Tetrahedra per molecule</td><td>Four-species tetrahedra (four-species systems) {c('S5')}</td><td>For the two-species runs no four-species tetrahedron exists; the new numbers count all 4-cliques of the molecule graph {c('N1')}</td><td>Compare two-species values only with each other (ideal crystal 0.358 applies to four species).</td></tr>
<tr><td>Statistics</td><td colspan="3">Most settings are single runs. The new K<sub>a</sub> &times; &alpha;, two-species and four-species results are n = 1; replicate scatter of the best-studied system is about 0.01 tetra/mol and nucleation can vary by two orders of magnitude between replicates {c('S1')}.</td></tr></table></div>

<h2 id="sources">7. Sources</h2>
<p>Tags used above. Published pages are on this site; dissertation files are in the <code>PhD-Dissertation</code> repository under <code>src/body/</code>; new-analysis files are in the <code>dna</code> repository under <code>large_crystal/hand5/final_report/</code> unless noted.</p>
<div class="tablewrap"><table>
<tr><th>Tag</th><th>Source</th><th>Used for</th></tr>
<tr><td id="src-S1">S1</td><td><a href="archive.html">archive.html</a></td><td>1,039 archive endpoints, K/T table, K<sub>far</sub> and &alpha; tables, PHB5 ladder, strength-variant energies, caveats on Hamiltonian and pre-formed seeds</td></tr>
<tr><td>S2</td><td><a href="hand5.html">hand5.html</a></td><td>stiffness, seeded, pre-connected, strength-scan, equal-K sweeps; ws vs ww; kick experiment</td></tr>
<tr><td>S3</td><td><a href="seeding.html">seeding.html</a></td><td>seed-size and temperature series, retraction of the critical-nucleus claim</td></tr>
<tr><td>S4</td><td><a href="window-scan.html">window-scan.html</a></td><td>quench holds, ramps, heating, melting near T = 0.165</td></tr>
<tr><td>S5</td><td><a href="method.html">method.html</a></td><td>model, patches, detector, classes, why energy is not evidence</td></tr>
<tr><td>S6</td><td><a href="corrections.html">corrections.html</a></td><td>corrections log D1&ndash;D23, E1&ndash;E9</td></tr>
<tr><td>S7</td><td><a href="about.html">about.html</a></td><td>literature list, reproducibility, limitations</td></tr>
<tr><td>S8</td><td><a href="gallery.html">gallery.html</a></td><td>new runs: K<sub>a</sub> &times; &alpha;, two species at higher T, four species, crystal slabs</td></tr>
<tr><td id="src-D1">D1</td><td><code>PHB_complete_analysis_2026-10-09.md</code></td><td>five findings, corrections, parameter verdicts, sweep summaries</td></tr>
<tr><td id="src-D2">D2</td><td><code>PHB_archive_findings.md</code></td><td>archive generations, strength variants, PHB4 &alpha; ladders (&sect;4.1&ndash;4.3)</td></tr>
<tr><td id="src-D3">D3</td><td><code>PHB_paper_roadmap.md</code></td><td>missing analyses A1&ndash;A5, B1&ndash;B7, C1&ndash;C3, D1&ndash;D6</td></tr>
<tr><td id="src-D4">D4</td><td><code>PHB_literature_review.md</code></td><td>literature context; cited works marked abstract-only there must be checked before citation (Liu et al. <i>Science</i> 2024; Hagan, Elrad, Jack 2011; Wang et al. <i>Nat. Commun.</i> 2015; Reinhardt and Frenkel 2014; Smallenburg and Sciortino 2013; Beneduce et al. 2023; Espinosa et al. 2016)</td></tr>
<tr><td id="src-D5">D5</td><td><code>PHB.tex</code> (dissertation chapter)</td><td>earlier statements that were later corrected</td></tr>
<tr><td id="src-N1">N1</td><td><code>findings/two_species.md</code> (&sect;4b)</td><td>two-species strength-design ranking</td></tr>
<tr><td id="src-N2">N2</td><td><code>findings/param_run.md</code></td><td>K<sub>b</sub>, temperature, strength, &alpha;, seed-size and protocol verdicts</td></tr>
<tr><td id="src-N3">N3</td><td><code>findings/param_ka.md</code></td><td>why the old K<sub>a</sub> sweep is unusable (step-counter splice)</td></tr>
<tr><td id="src-N4">N4</td><td><code>large_crystal/PHB_visuals_2026-10-23/analysis/</code>, <code>OPS_LOG_2026-10-15.md</code></td><td>K<sub>a</sub> &times; &alpha; and two-species tables and figures; queued jobs</td></tr></table></div>
<p class="tag foot">Part of the PHB study (oxDNAcpp). Synthesis written 2026-10-23 from the sources listed; numbers are quoted from them, not recomputed, except where tagged S8/N1/N4.</p>
</main></div>
<div id="lb" hidden><img alt=""><p></p></div>
<script src="site.js"></script></body></html>"""
nav = re.search(r'<nav class="site".*?</nav>', (P / "index.html").read_text(), re.S).group(0)
nav = re.sub(r' class=on', '', nav)
if 'summary.html' not in nav:
    nav = nav.replace('<a href="archive.html"', '<a href="summary.html" class=on>Summary</a><a href="archive.html"', 1)
else:
    nav = nav.replace('<a href="summary.html">', '<a href="summary.html" class=on>')
H = H.replace("@@NAV@@", nav)
(P / "summary.html").write_text(H)
print("bytes", len(H))
