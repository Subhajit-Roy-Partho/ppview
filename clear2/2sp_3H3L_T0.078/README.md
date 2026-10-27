# 2sp_3H3L_T0.078

**2-species 3H3L, T=0.078**  
Series: 2-species, T = 0.078 (stopped)

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `2sp_3H3L_T0.078_initial_ballstick.png` | starting configuration |
| `2sp_3H3L_T0.078_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 5000 | 0 of 500 (0.0%) | 0 |
| last | 1.655e+09 | 92 of 500 (18.4%) | 23 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/hand5/two_species_preconnected/3H3L/Kb_300_T_0.078`
* topology: `/scratch/sroy85/Github/dna/large_crystal/hand5/two_species_preconnected/topology_3H3L.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input`): backend = CUDA, interaction_type = PHB, steps = 1500000000, dt = 0.0005, thermostat = john, T = 0.078, rcut = 2.0, patchyAlpha = 0.12, Ka = 300, Kb = 300
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/two_species_preconnected/3H3L/Kb_300_T_0.078/mc_relaxed.dat` (step 5000)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/two_species_preconnected/3H3L/Kb_300_T_0.078/final_conf.dat` (step 1.655e+09, file last written 2026-10-15 12:17; the run may have continued since)

## Regenerate

```
python clear2/render_clear2.py run 2sp_3H3L_T0.078
```
