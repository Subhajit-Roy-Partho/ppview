# pd-anneal-SM-SM_smoke_T0.138

**phase_diagram/anneal/SM/SM_smoke_T0.138 (T=0.138)**  
Series: best of study phase_diagram/anneal/SM

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Arms bind cores through complementary patches (colours c and -c). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders: no title, legend, axes or periodic box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration | model |
|---|---|---|
| `pd-anneal-SM-SM_smoke_T0.138_initial_ball.png` | starting configuration | ppview ball model: cores and arm beads as spheres |
| `pd-anneal-SM-SM_smoke_T0.138_initial_ballstick.png` | starting configuration | ball-and-stick: core balls, arm joint balls joined by sticks |
| `pd-anneal-SM-SM_smoke_T0.138_final_ball.png` | last configuration | ppview ball model: cores and arm beads as spheres |
| `pd-anneal-SM-SM_smoke_T0.138_final_ballstick.png` | last configuration | ball-and-stick: core balls, arm joint balls joined by sticks |

Colours: cores are grey; arm beads/sticks are slate; each patch on a core is coloured by its interaction colour id, and a complementary pair (c, -c) shares one colour, so two bonded cores show a matching coloured patch where they touch. Hue is keyed on |c| mod 500; the darker variant marks |c| >= 500 (the strong channels).

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/SM/SM_smoke_T0.138`
* topology: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/SM/SM_smoke_T0.138/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 8300000, dt = 0.0005, thermostat = john, T = 0.138, rcut = 2.0, patchyAlpha = 0.1, Ka = 300, Kb = 300, seed = 40911
* staged protocol (`stages.txt`: temperature, steps): T=0.138 x 10,000,000
* run metadata (`meta.json`): `{"topology": "/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_K300_large/weak_weak/Kb_300_T_0.078/topology.phb", "conf": "/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_K300_large/weak_weak/Kb_300_T_0.078/final_conf.dat", "stages": [[0.138, 10000000]], "alpha": 0.1, "ka": 300, "kb": 300, "dt": 0.0005, "seed": 31631, "core_weak": 1, "tip_weak": 1, "n_patches_rewritten": 36, "study": "anneal-SM", "K": 2, "replicate": 1, "purpose": "smoke K=2 dt=5e-4 at T=0.138", "smoke_test": true, "dt_note": "standard dt=5e-4 (all T<=0.2)"}`
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/SM/SM_smoke_T0.138/mc_relaxed.dat` (step 9.263e+08; the configuration the MD started from, after the short MC relaxation where one was run)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/SM/SM_smoke_T0.138/final_conf.dat` (step 9.363e+08, file last written 2026-10-24 06:49; the run may have continued since)

## Structure at the two configurations

Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`.

| | step | largest cluster | clusters | mean valence (max 6) | six-valent molecules | intact tetrahedra per molecule |
|---|---|---|---|---|---|---|
| start | 9.263e+08 | 100.0% | 1 | 4.06 | 9.8% | 0.112 |
| last | 9.363e+08 | 100.0% | 1 | 3.91 | 8.4% | 0.104 |

(ideal crystal: 0.358 tetrahedra per molecule, six-valent 100%)

## Regenerate

```
python hclear/render_clear.py run pd-anneal-SM-SM_smoke_T0.138
```
or directly: `python render_phb.py --top <topology> --conf <conf> --out img.png --width 3200 --height 2400 --model ball|ballstick`.
