# pd-hetero-H3-H3_a0.15_r1

**phase_diagram/hetero/H3/H3_a0.15_r1 (T=0.14)**  
Series: Best temperature of its system

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Arms bind cores through complementary patches (colours c and -c). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders: no title, legend, axes or periodic box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration | model |
|---|---|---|
| `pd-hetero-H3-H3_a0.15_r1_initial_ball.png` | starting configuration | ppview ball model: cores and arm beads as spheres |
| `pd-hetero-H3-H3_a0.15_r1_initial_ballstick.png` | starting configuration | ball-and-stick: core balls, arm joint balls joined by sticks |
| `pd-hetero-H3-H3_a0.15_r1_final_ball.png` | last configuration | ppview ball model: cores and arm beads as spheres |
| `pd-hetero-H3-H3_a0.15_r1_final_ballstick.png` | last configuration | ball-and-stick: core balls, arm joint balls joined by sticks |

Colours: cores are grey; arm beads/sticks are slate; each patch on a core is coloured by its interaction colour id, and a complementary pair (c, -c) shares one colour, so two bonded cores show a matching coloured patch where they touch. Hue is keyed on |c| mod 500; the darker variant marks |c| >= 500 (the strong channels).

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/hetero/H3/H3_a0.15_r1`
* topology: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/hetero/H3/H3_a0.15_r1/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 1350605000, dt = 0.0005, thermostat = john, T = 0.14, rcut = 2.0, patchyAlpha = 0.15, Ka = 300, Kb = 300, seed = 19551
* staged protocol (`stages.txt`: temperature, steps): T=0.14 x 2,000,000,000
* run metadata (`meta.json`): `{"topology": "/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/S128_T0.140_r2/topology.phb", "conf": "/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/S128_T0.140_r2/start_conf.dat", "stages": [[0.14, 2000000000]], "alpha": 0.15, "ka": 300, "kb": 300, "dt": 0.0005, "seed": 13057, "core_weak": 1, "tip_weak": 1, "n_patches_rewritten": 36, "study": "hetero-H3", "K": 2, "replicate": 1, "purpose": "patch-width scan", "smoke_test": false, "dt_note": "standard dt (T<=0.2)"}`
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/hetero/H3/H3_a0.15_r1/mc_relaxed.dat` (step 5000; the configuration the MD started from, after the short MC relaxation where one was run)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/hetero/H3/H3_a0.15_r1/final_conf.dat` (step 6.724e+08, file last written 2026-10-26 18:33; the run may have continued since)

## Structure at the two configurations

Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`.

| | step | largest cluster | clusters | mean valence (max 6) | six-valent molecules | intact tetrahedra per molecule |
|---|---|---|---|---|---|---|
| start | 5000 | 25.6% | 1 | 1.20 | 10.6% | 0.086 |
| last | 6.724e+08 | 99.6% | 1 | 4.52 | 31.8% | 0.252 |

(ideal crystal: 0.358 tetrahedra per molecule, six-valent 100%)

## Regenerate

```
python hclear/render_clear.py run pd-hetero-H3-H3_a0.15_r1
```
or directly: `python render_phb.py --top <topology> --conf <conf> --out img.png --width 3200 --height 2400 --model ball|ballstick`.
