# preconnected_strength_scan-S50-Kb_300_T_0.100

**hand5/preconnected_strength_scan/S50/Kb_300_T_0.100 (T=0.100)**  
Series: best of study hand5/preconnected_strength_scan

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Arms bind cores through complementary patches (colours c and -c). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders: no title, legend, axes or periodic box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration | model |
|---|---|---|
| `preconnected_strength_scan-S50-Kb_300_T_0.100_initial_ball.png` | starting configuration | ppview ball model: cores and arm beads as spheres |
| `preconnected_strength_scan-S50-Kb_300_T_0.100_initial_ballstick.png` | starting configuration | ball-and-stick: core balls, arm joint balls joined by sticks |
| `preconnected_strength_scan-S50-Kb_300_T_0.100_final_ball.png` | last configuration | ppview ball model: cores and arm beads as spheres |
| `preconnected_strength_scan-S50-Kb_300_T_0.100_final_ballstick.png` | last configuration | ball-and-stick: core balls, arm joint balls joined by sticks |

Colours: cores are grey; arm beads/sticks are slate; each patch on a core is coloured by its interaction colour id, and a complementary pair (c, -c) shares one colour, so two bonded cores show a matching coloured patch where they touch. Hue is keyed on |c| mod 500; the darker variant marks |c| >= 500 (the strong channels).

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_strength_scan/S50/Kb_300_T_0.100`
* topology: `/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_strength_scan/S50/Kb_300_T_0.100/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input`): backend = CUDA, interaction_type = PHB, steps = 1500000000, dt = 0.0005, thermostat = john, T = 0.100, rcut = 2.0, patchyAlpha = 0.12, Ka = 300, Kb = 300
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_strength_scan/S50/Kb_300_T_0.100/mc_relaxed.dat` (step 5000; the configuration the MD started from, after the short MC relaxation where one was run)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_strength_scan/S50/Kb_300_T_0.100/final_conf.dat` (step 1.962e+09, file last written 2026-10-11 22:08; the run may have continued since)

## Structure at the two configurations

Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`.

| | step | largest cluster | clusters | mean valence (max 6) | six-valent molecules | intact tetrahedra per molecule |
|---|---|---|---|---|---|---|
| start | 5000 | 6.4% | 1 | 0.25 | 1.8% | 0.020 |
| last | 1.962e+09 | 100.0% | 1 | 4.17 | 11.0% | 0.124 |

(ideal crystal: 0.358 tetrahedra per molecule, six-valent 100%)

## Regenerate

```
python hclear/render_clear.py run preconnected_strength_scan-S50-Kb_300_T_0.100
```
or directly: `python render_phb.py --top <topology> --conf <conf> --out img.png --width 3200 --height 2400 --model ball|ballstick`.
