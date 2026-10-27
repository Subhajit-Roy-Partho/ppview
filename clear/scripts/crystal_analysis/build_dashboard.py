#!/usr/bin/env python3
"""
Unified dashboard combining crystal analysis and energy plots into a single
self-contained HTML file.
"""
import base64
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
PLOTS = HERE / "plots"

def png_to_b64(path):
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def img_tag(b64, alt, cls="plot-img"):
    if b64 is None:
        return f'<div class="missing">Missing: {alt}</div>'
    return f'<img src="data:image/png;base64,{b64}" class="{cls}" alt="{alt}'

# Load crystal results
with open(HERE / "results.json") as f:
    raw = json.load(f)

seen = {}
for r in raw:
    key = (r["sweep"], r["patch_set"], round(r["Kb"]), round(r["T"], 3))
    if key not in seen or r.get("ok"):
        seen[key] = r
results = [r for r in seen.values() if r.get("ok")]

# Load energy stats
with open(PLOTS / "energy_stats.json") as f:
    energy_stats = json.load(f)

# Collect all images
imgs = {}
for name in [
    "stiffness_heatmaps", "stiffness_valence", "seeded_heatmaps",
    "preconnected", "comparison_lines",
    "energy_stiffness_weak_weak", "energy_stiffness_weak_strong",
    "energy_seeded_weak_weak", "energy_seeded_weak_strong",
    "energy_stiffness_grid_ww", "energy_stiffness_grid_ws",
    "energy_seeded_grid_ww", "energy_seeded_grid_ws",
    "energy_bars_stiffness_ww", "energy_bars_stiffness_ws",
    "energy_bars_seeded_ww", "energy_bars_seeded_ws",
]:
    imgs[name] = png_to_b64(PLOTS / f"{name}.png")

# Summary stats for crystal
def crystal_stats():
    rows = []
    for sweep in ("stiffness_sweep", "seeded_sweep", "preconnected"):
        for pset in ("weak_weak", "weak_strong", "four_species"):
            subset = [r for r in results if r["sweep"] == sweep and r["patch_set"] == pset]
            if not subset:
                continue
            lc_vals = [r["crystal"]["largest_cluster_fraction"]*100 for r in subset]
            av_vals = [r["crystal"]["avg_valence"] for r in subset]
            rows.append({
                "sweep": sweep.replace("_", " "),
                "patch_set": pset.replace("_", "-"),
                "n": len(subset),
                "lc_mean": float(np.mean(lc_vals)),
                "lc_min": float(np.min(lc_vals)),
                "lc_max": float(np.max(lc_vals)),
                "av_mean": float(np.mean(av_vals)),
            })
    return rows

def energy_summary():
    rows = []
    for sweep in ("stiffness_sweep", "seeded_sweep", "preconnected"):
        for pset in ("weak_weak", "weak_strong", "four_species"):
            subset = [s for s in energy_stats if s["sweep"] == sweep and s["patch_set"] == pset]
            if not subset:
                continue
            pe_finals = [s["pe_final"] for s in subset]
            t_maxes = [s["t_max"] for s in subset]
            rows.append({
                "sweep": sweep.replace("_", " "),
                "patch_set": pset.replace("_", "-"),
                "n": len(subset),
                "pe_final_mean": float(np.mean(pe_finals)),
                "pe_final_min": float(np.min(pe_finals)),
                "pe_final_max": float(np.max(pe_finals)),
                "t_max": float(np.max(t_maxes)),
                "t_avg": float(np.mean(t_maxes)),
            })
    return rows

c_stats = crystal_stats()
e_stats = energy_summary()

html = f"""<title>PHB Crystal & Energy Dashboard</title>
<style>
  :root {{
    --bg: #f8fafc; --card: #ffffff; --border: #e2e8f0;
    --text: #1e293b; --muted: #64748b; --accent: #3158b3;
    --tag-bg: #eff6ff; --tag-text: #1d4ed8;
  }}
  [data-theme="dark"] {{
    --bg: #0f172a; --card: #1e293b; --border: #334155;
    --text: #f1f5f9; --muted: #94a3b8; --accent: #8fa9e0;
    --tag-bg: #1e3a5f; --tag-text: #93c5fd;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; font-size: 14px; line-height: 1.5; }}
  .header {{ background: var(--card); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
  .header h1 {{ font-size: 18px; font-weight: 700; color: var(--accent); }}
  .header .sub {{ font-size: 12px; color: var(--muted); margin-top: 2px; }}
  .toggle-btn {{ background: var(--tag-bg); color: var(--tag-text); border: 1px solid var(--border); border-radius: 6px; padding: 6px 12px; cursor: pointer; font-size: 12px; font-weight: 600; }}
  .main {{ max-width: 1200px; margin: 0 auto; padding: 24px 16px; }}
  .section {{ margin-bottom: 32px; }}
  .section-title {{ font-size: 15px; font-weight: 700; margin-bottom: 4px; padding-bottom: 8px; border-bottom: 2px solid var(--accent); display: inline-block; }}
  .section-desc {{ font-size: 12px; color: var(--muted); margin-bottom: 14px; margin-top: 4px; }}
  .plot-img {{ width: 100%; border-radius: 8px; border: 1px solid var(--border); background: var(--card); display: block; margin-bottom: 12px; }}
  .missing {{ padding: 20px; text-align: center; color: var(--muted); background: var(--card); border: 1px dashed var(--border); border-radius: 8px; }}
  .tabs {{ display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }}
  .tab {{ padding: 6px 14px; border-radius: 20px; cursor: pointer; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--card); color: var(--muted); transition: all .15s; }}
  .tab.active {{ background: var(--accent); color: white; border-color: var(--accent); }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-top: 12px; }}
  .stat-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }}
  .stat-card .sc-sweep {{ font-size: 11px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }}
  .stat-card .sc-pset {{ font-size: 12px; color: var(--muted); margin-bottom: 8px; }}
  .stat-row {{ display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid var(--border); font-size: 13px; }}
  .stat-row:last-child {{ border: none; }}
  .stat-val {{ font-weight: 700; color: var(--text); }}
  .note {{ background: var(--tag-bg); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; font-size: 12px; color: var(--muted); margin-top: 10px; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; background: var(--tag-bg); color: var(--tag-text); margin-left: 6px; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  @media (max-width: 768px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
</style>

<div class="header">
  <div>
    <h1>PHB Crystal &amp; Energy Dashboard</h1>
    <div class="sub">hand5 simulations - 148 runs across stiffness, seeded, and preconnected sweeps</div>
  </div>
  <button class="toggle-btn" onclick="toggleDark()">Toggle dark mode</button>
</div>

<div class="main">

  <!-- Crystal Summary -->
  <div class="section">
    <div class="section-title">Crystal Summary</div>
    <div class="section-desc">Largest cluster fraction and average valence from final_conf.dat checkpoints.</div>
    <div class="stats-grid" id="crystal-stats"></div>
  </div>

  <!-- Energy Summary -->
  <div class="section">
    <div class="section-title">Energy Summary</div>
    <div class="section-desc">Final potential energy per particle and simulation progress.</div>
    <div class="stats-grid" id="energy-stats"></div>
  </div>

  <!-- Crystal heatmaps -->
  <div class="section">
    <div class="section-title">Crystal Quality Heatmaps <span class="badge">Stiffness sweep</span></div>
    <div class="section-desc">Color = metric; rows = K<sub>b</sub>; columns = T.</div>
    <div class="tabs">
      <div class="tab active" onclick="showTab('lc',event)">Largest cluster %</div>
      <div class="tab" onclick="showTab('val',event)">Avg valence</div>
      <div class="tab" onclick="showTab('seeded',event)">Seeded sweep</div>
    </div>
    <div id="tab-lc" class="tab-content active">
      {img_tag(imgs['stiffness_heatmaps'], 'Stiffness heatmaps')}
    </div>
    <div id="tab-val" class="tab-content">
      {img_tag(imgs['stiffness_valence'], 'Stiffness valence')}
    </div>
    <div id="tab-seeded" class="tab-content">
      {img_tag(imgs['seeded_heatmaps'], 'Seeded heatmaps')}
      <div class="note">Seeded simulations are at early stage. Low cluster fractions reflect the seed cluster only; crystal growth is diffusion-limited and ongoing.</div>
    </div>
  </div>

  <!-- Crystal comparison lines -->
  <div class="section">
    <div class="section-title">LC fraction vs Temperature</div>
    <div class="section-desc">Each line = one K<sub>b</sub> value across temperatures.</div>
    {img_tag(imgs['comparison_lines'], 'Comparison lines')}
  </div>

  <!-- Preconnected -->
  <div class="section">
    <div class="section-title">Preconnected seed sweep</div>
    <div class="section-desc">4 temperature points at K<sub>b</sub>=300 with four-species preconnected seed.</div>
    {img_tag(imgs['preconnected'], 'Preconnected')}
  </div>

  <!-- Energy vs Time -->
  <div class="section">
    <div class="section-title">Energy vs Time <span class="badge">PE/N trajectories</span></div>
    <div class="section-desc">Potential energy per particle over simulation time. Each panel = one K<sub>b</sub>; lines = temperatures.</div>
    <div class="tabs">
      <div class="tab active" onclick="showTab('e_sww',event)">Stiffness W-W</div>
      <div class="tab" onclick="showTab('e_sws',event)">Stiffness W-S</div>
      <div class="tab" onclick="showTab('e_sdw',event)">Seeded W-W</div>
      <div class="tab" onclick="showTab('e_sds',event)">Seeded W-S</div>
    </div>
    <div id="tab-e_sww" class="tab-content active">
      {img_tag(imgs['energy_stiffness_weak_weak'], 'Energy stiffness weak-weak')}
    </div>
    <div id="tab-e_sws" class="tab-content">
      {img_tag(imgs['energy_stiffness_weak_strong'], 'Energy stiffness weak-strong')}
    </div>
    <div id="tab-e_sdw" class="tab-content">
      {img_tag(imgs['energy_seeded_weak_weak'], 'Energy seeded weak-weak')}
    </div>
    <div id="tab-e_sds" class="tab-content">
      {img_tag(imgs['energy_seeded_weak_strong'], 'Energy seeded weak-strong')}
    </div>
  </div>

  <!-- Energy grid plots -->
  <div class="section">
    <div class="section-title">Energy Grid Views</div>
    <div class="section-desc">6x6 grid (rows=K<sub>b</sub>, cols=T) showing PE/N trajectory for each parameter combination.</div>
    <div class="tabs">
      <div class="tab active" onclick="showTab('g_sww',event)">Stiffness W-W grid</div>
      <div class="tab" onclick="showTab('g_sws',event)">Stiffness W-S grid</div>
      <div class="tab" onclick="showTab('g_sdw',event)">Seeded W-W grid</div>
      <div class="tab" onclick="showTab('g_sds',event)">Seeded W-S grid</div>
    </div>
    <div id="tab-g_sww" class="tab-content active">
      {img_tag(imgs['energy_stiffness_grid_ww'], 'Energy stiffness grid ww')}
    </div>
    <div id="tab-g_sws" class="tab-content">
      {img_tag(imgs['energy_stiffness_grid_ws'], 'Energy stiffness grid ws')}
    </div>
    <div id="tab-g_sdw" class="tab-content">
      {img_tag(imgs['energy_seeded_grid_ww'], 'Energy seeded grid ww')}
    </div>
    <div id="tab-g_sds" class="tab-content">
      {img_tag(imgs['energy_seeded_grid_ws'], 'Energy seeded grid ws')}
    </div>
  </div>

  <!-- Energy bars -->
  <div class="section">
    <div class="section-title">Final PE/N Bar Charts</div>
    <div class="section-desc">Final potential energy per particle for each (K<sub>b</sub>, T) combination.</div>
    <div class="two-col">
      {img_tag(imgs['energy_bars_stiffness_ww'], 'Energy bars stiffness ww')}
      {img_tag(imgs['energy_bars_stiffness_ws'], 'Energy bars stiffness ws')}
    </div>
    <div class="two-col" style="margin-top:12px">
      {img_tag(imgs['energy_bars_seeded_ww'], 'Energy bars seeded ww')}
      {img_tag(imgs['energy_bars_seeded_ws'], 'Energy bars seeded ws')}
    </div>
  </div>

</div>

<script>
var cStats = {json.dumps(c_stats)};
var eStats = {json.dumps(e_stats)};

function toggleDark() {{
  var el = document.documentElement;
  el.setAttribute('data-theme', el.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}}

function showTab(id, evt) {{
  document.querySelectorAll('.tab-content').forEach(function(el) {{ el.classList.remove('active'); }});
  document.querySelectorAll('.tab').forEach(function(el) {{ el.classList.remove('active'); }});
  document.getElementById('tab-' + id).classList.add('active');
  if (evt) evt.target.classList.add('active');
}}

function sweepLabel(s) {{
  return {{stiffness_sweep:'Stiffness',seeded_sweep:'Seeded',preconnected:'Preconnected'}}[s] || s;
}}

var cgrid = document.getElementById('crystal-stats');
cStats.forEach(function(s) {{
  var div = document.createElement('div');
  div.className = 'stat-card';
  div.innerHTML =
    '<div class="sc-sweep">' + sweepLabel(s.sweep) + '</div>' +
    '<div class="sc-pset">' + s.patch_set + ' (' + s.n + ' sims)</div>' +
    '<div class="stat-row"><span>Largest cluster</span><span class="stat-val">' + s.lc_mean.toFixed(1) + '% <small style="font-weight:normal;color:var(--muted)">(' + s.lc_min.toFixed(1) + '-' + s.lc_max.toFixed(1) + '%)</small></span></div>' +
    '<div class="stat-row"><span>Avg valence</span><span class="stat-val">' + s.av_mean.toFixed(2) + ' / 6</span></div>';
  cgrid.appendChild(div);
}});

var egrid = document.getElementById('energy-stats');
eStats.forEach(function(s) {{
  var div = document.createElement('div');
  div.className = 'stat-card';
  div.innerHTML =
    '<div class="sc-sweep">' + sweepLabel(s.sweep) + '</div>' +
    '<div class="sc-pset">' + s.patch_set + ' (' + s.n + ' sims)</div>' +
    '<div class="stat-row"><span>Final PE/N</span><span class="stat-val">' + s.pe_final_mean.toFixed(2) + ' <small style="font-weight:normal;color:var(--muted)">(' + s.pe_final_min.toFixed(1) + '-' + s.pe_final_max.toFixed(1) + ')</small></span></div>' +
    '<div class="stat-row"><span>Max time</span><span class="stat-val">' + s.t_max.toFixed(0) + ' sim units</span></div>';
  egrid.appendChild(div);
}});
</script>
"""

html_path = PLOTS / "dashboard.html"
html_path.write_text(html)
print(f"  -> dashboard.html ({html_path.stat().st_size // 1024} KB)")
