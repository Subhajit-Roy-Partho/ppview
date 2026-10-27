# 4sp_ws_T0.140

**4-species weak-strong (K~101), T=0.14, 32-seed**  
Series: 4-species preconnected

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `4sp_ws_T0.140_initial_ballstick.png` | starting configuration |
| `4sp_ws_T0.140_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 5000 | 31 of 500 (6.2%) | 10 |
| last | 4.072e+08 | 151 of 500 (30.2%) | 43 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_K300_large/weak_strong/Kb_300_T_0.140`
* topology: `/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_K300_large/base_weak_strong.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input`): backend = CUDA, interaction_type = PHB, steps = 1500000000, dt = 0.0005, thermostat = john, T = 0.140, rcut = 2.0, patchyAlpha = 0.1, Ka = 300, Kb = 300
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_K300_large/weak_strong/Kb_300_T_0.140/mc_relaxed.dat` (step 5000)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/preconnected_K300_large/weak_strong/Kb_300_T_0.140/final_conf.dat` (step 4.072e+08, file last written 2026-10-26 17:45; the run may have continued since)

## Regenerate

```
python clear2/render_clear2.py run 4sp_ws_T0.140
```
