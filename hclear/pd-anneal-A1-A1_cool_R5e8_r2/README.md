# pd-anneal-A1-A1_cool_R5e8_r2

**phase_diagram/anneal/A1/A1_cool_R5e8_r2 (T=0.13)**  
Series: best of study phase_diagram/anneal/A1

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Arms bind cores through complementary patches (colours c and -c). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders: no title, legend, axes or periodic box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration | model |
|---|---|---|
| `pd-anneal-A1-A1_cool_R5e8_r2_initial_ball.png` | starting configuration | ppview ball model: cores and arm beads as spheres |
| `pd-anneal-A1-A1_cool_R5e8_r2_initial_ballstick.png` | starting configuration | ball-and-stick: core balls, arm joint balls joined by sticks |
| `pd-anneal-A1-A1_cool_R5e8_r2_final_ball.png` | last configuration | ppview ball model: cores and arm beads as spheres |
| `pd-anneal-A1-A1_cool_R5e8_r2_final_ballstick.png` | last configuration | ball-and-stick: core balls, arm joint balls joined by sticks |

Colours: cores are grey; arm beads/sticks are slate; each patch on a core is coloured by its interaction colour id, and a complementary pair (c, -c) shares one colour, so two bonded cores show a matching coloured patch where they touch. Hue is keyed on |c| mod 500; the darker variant marks |c| >= 500 (the strong channels).

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A1/A1_cool_R5e8_r2`
* topology: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A1/A1_cool_R5e8_r2/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 134300000, dt = 0.0005, thermostat = john, T = 0.13, rcut = 2.0, patchyAlpha = 0.1, Ka = 300, Kb = 300, seed = 50021
* staged protocol (`stages.txt`: temperature, steps): T=0.19 x 300,000,000; T=0.19 x 20,000,000; T=0.1875 x 20,000,000; T=0.185 x 20,000,000; T=0.1825 x 20,000,000; T=0.18 x 20,000,000; T=0.1775 x 20,000,000; T=0.175 x 20,000,000; T=0.1725 x 20,000,000; T=0.17 x 20,000,000; T=0.1675 x 20,000,000; T=0.165 x 20,000,000; T=0.1625 x 20,000,000; T=0.16 x 20,000,000; T=0.1575 x 20,000,000; T=0.155 x 20,000,000; T=0.1525 x 20,000,000; T=0.15 x 20,000,000; T=0.1475 x 20,000,000; T=0.145 x 20,000,000; T=0.1425 x 20,000,000; T=0.14 x 20,000,000; T=0.1375 x 20,000,000; T=0.135 x 20,000,000; T=0.1325 x 20,000,000; T=0.13 x 20,000,000; T=0.13 x 300,000,000
* run metadata (`meta.json`): `{"topology": "/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_K300_large/weak_weak/Kb_300_T_0.078/topology.phb", "conf": "/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_K300_large/weak_weak/Kb_300_T_0.078/final_conf.dat", "stages": [[0.19, 300000000], [0.19, 20000000], [0.1875, 20000000], [0.185, 20000000], [0.1825, 20000000], [0.18, 20000000], [0.1775, 20000000], [0.175, 20000000], [0.1725, 20000000], [0.17, 20000000], [0.1675, 20000000], [0.165, 20000000], [0.1625, 20000000], [0.16, 20000000], [0.1575, 20000000], [0.155, 20000000], [0.1525, 20000000], [0.15, 20000000`
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A1/A1_cool_R5e8_r2/mc_relaxed.dat` (step 9.263e+08; the configuration the MD started from, after the short MC relaxation where one was run)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A1/A1_cool_R5e8_r2/final_conf.dat` (step 1.944e+09, file last written 2026-10-26 18:37; the run may have continued since)

## Structure at the two configurations

Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`.

| | step | largest cluster | clusters | mean valence (max 6) | six-valent molecules | intact tetrahedra per molecule |
|---|---|---|---|---|---|---|
| start | 9.263e+08 | 100.0% | 1 | 4.06 | 9.8% | 0.112 |
| last | 1.944e+09 | 90.0% | 9 | 3.31 | 4.8% | 0.086 |

(ideal crystal: 0.358 tetrahedra per molecule, six-valent 100%)

## Regenerate

```
python hclear/render_clear.py run pd-anneal-A1-A1_cool_R5e8_r2
```
or directly: `python render_phb.py --top <topology> --conf <conf> --out img.png --width 3200 --height 2400 --model ball|ballstick`.
