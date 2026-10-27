# pd-melting-M2-M2_L40_T0.13

**phase_diagram/melting/M2/M2_L40_T0.13 (T=0.13)**  
Series: best of study phase_diagram/melting/M2

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Arms bind cores through complementary patches (colours c and -c). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders: no title, legend, axes or periodic box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration | model |
|---|---|---|
| `pd-melting-M2-M2_L40_T0.13_initial_ball.png` | starting configuration | ppview ball model: cores and arm beads as spheres |
| `pd-melting-M2-M2_L40_T0.13_initial_ballstick.png` | starting configuration | ball-and-stick: core balls, arm joint balls joined by sticks |
| `pd-melting-M2-M2_L40_T0.13_final_ball.png` | last configuration | ppview ball model: cores and arm beads as spheres |
| `pd-melting-M2-M2_L40_T0.13_final_ballstick.png` | last configuration | ball-and-stick: core balls, arm joint balls joined by sticks |

Colours: cores are grey; arm beads/sticks are slate; each patch on a core is coloured by its interaction colour id, and a complementary pair (c, -c) shares one colour, so two bonded cores show a matching coloured patch where they touch. Hue is keyed on |c| mod 500; the darker variant marks |c| >= 500 (the strong channels).

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M2/M2_L40_T0.13`
* topology: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M2/M2_L40_T0.13/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 795000000, dt = 0.0005, thermostat = john, T = 0.13, rcut = 2.0, patchyAlpha = 0.1, Ka = 300, Kb = 300, seed = 29157
* staged protocol (`stages.txt`: temperature, steps): T=0.13 x 1,500,000,000
* run metadata (`meta.json`): `{"topology": "/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/S128_T0.140_r2/topology.phb", "conf": "/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/confs/placement_M2_L40.dat", "stages": [[0.13, 1500000000]], "alpha": 0.1, "ka": 300, "kb": 300, "dt": 0.0005, "seed": 22107, "core_weak": 1, "tip_weak": 1, "n_patches_rewritten": 36, "study": "melting-M2", "K": 2, "replicate": 1, "purpose": "M2 seeded growth/dissolution L=40 T=0.13", "smoke_test": false, "dt_note": "standard dt (T<=0.2)"}`
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M2/M2_L40_T0.13/mc_relaxed.dat` (step 0; the configuration the MD started from, after the short MC relaxation where one was run)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M2/M2_L40_T0.13/final_conf.dat` (step 7.415e+08, file last written 2026-10-26 18:44; the run may have continued since)

## Structure at the two configurations

Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`.

| | step | largest cluster | clusters | mean valence (max 6) | six-valent molecules | intact tetrahedra per molecule |
|---|---|---|---|---|---|---|
| start | 0 | 25.6% | 1 | 1.20 | 10.6% | 0.086 |
| last | 7.415e+08 | 96.8% | 3 | 4.12 | 23.2% | 0.208 |

(ideal crystal: 0.358 tetrahedra per molecule, six-valent 100%)

## Regenerate

```
python hclear/render_clear.py run pd-melting-M2-M2_L40_T0.13
```
or directly: `python render_phb.py --top <topology> --conf <conf> --out img.png --width 3200 --height 2400 --model ball|ballstick`.
