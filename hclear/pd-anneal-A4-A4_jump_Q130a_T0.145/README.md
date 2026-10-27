# pd-anneal-A4-A4_jump_Q130a_T0.145

**phase_diagram/anneal/A4/A4_jump_Q130a_T0.145 (T=0.145)**  
Series: best of study phase_diagram/anneal/A4

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Arms bind cores through complementary patches (colours c and -c). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders: no title, legend, axes or periodic box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration | model |
|---|---|---|
| `pd-anneal-A4-A4_jump_Q130a_T0.145_initial_ball.png` | starting configuration | ppview ball model: cores and arm beads as spheres |
| `pd-anneal-A4-A4_jump_Q130a_T0.145_initial_ballstick.png` | starting configuration | ball-and-stick: core balls, arm joint balls joined by sticks |
| `pd-anneal-A4-A4_jump_Q130a_T0.145_final_ball.png` | last configuration | ppview ball model: cores and arm beads as spheres |
| `pd-anneal-A4-A4_jump_Q130a_T0.145_final_ballstick.png` | last configuration | ball-and-stick: core balls, arm joint balls joined by sticks |

Colours: cores are grey; arm beads/sticks are slate; each patch on a core is coloured by its interaction colour id, and a complementary pair (c, -c) shares one colour, so two bonded cores show a matching coloured patch where they touch. Hue is keyed on |c| mod 500; the darker variant marks |c| >= 500 (the strong channels).

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A4/A4_jump_Q130a_T0.145`
* topology: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A4/A4_jump_Q130a_T0.145/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 1384005000, dt = 0.0005, thermostat = john, T = 0.145, rcut = 2.0, patchyAlpha = 0.1, Ka = 300, Kb = 300, seed = 45686
* staged protocol (`stages.txt`: temperature, steps): T=0.145 x 2,000,000,000
* run metadata (`meta.json`): `{"topology": "/scratch/sroy85/Github/dna/large_crystal/hand5/window_scan/runs/Q_T0.130_a/topology.phb", "conf": "/scratch/sroy85/Github/dna/large_crystal/hand5/window_scan/runs/Q_T0.130_a/final_conf.dat", "stages": [[0.145, 2000000000]], "alpha": 0.1, "ka": 300, "kb": 300, "dt": 0.0005, "seed": 31426, "core_weak": 1, "tip_weak": 1, "n_patches_rewritten": 36, "study": "anneal-A4", "K": 2, "replicate": 1, "purpose": "A4 aggregate Q130a jumped to T=0.145", "smoke_test": false, "dt_note": "standard dt=5e-4 (all T<=0.2)"}`
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A4/A4_jump_Q130a_T0.145/mc_relaxed.dat` (step 8.1e+08; the configuration the MD started from, after the short MC relaxation where one was run)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A4/A4_jump_Q130a_T0.145/final_conf.dat` (step 1.426e+09, file last written 2026-10-25 12:45; the run may have continued since)

## Structure at the two configurations

Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`.

| | step | largest cluster | clusters | mean valence (max 6) | six-valent molecules | intact tetrahedra per molecule |
|---|---|---|---|---|---|---|
| start | 8.1e+08 | 97.8% | 2 | 3.80 | 12.2% | 0.146 |
| last | 1.426e+09 | 38.4% | 21 | 3.17 | 15.2% | 0.184 |

(ideal crystal: 0.358 tetrahedra per molecule, six-valent 100%)

## Regenerate

```
python hclear/render_clear.py run pd-anneal-A4-A4_jump_Q130a_T0.145
```
or directly: `python render_phb.py --top <topology> --conf <conf> --out img.png --width 3200 --height 2400 --model ball|ballstick`.
