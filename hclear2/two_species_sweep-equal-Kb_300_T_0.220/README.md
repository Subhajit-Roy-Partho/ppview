# two_species_sweep-equal-Kb_300_T_0.220

**hand5/two_species_sweep/equal/Kb_300_T_0.220 (T=0.220)**  
Series: best of study hand5/two_species_sweep

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `two_species_sweep-equal-Kb_300_T_0.220_initial_ballstick.png` | starting configuration |
| `two_species_sweep-equal-Kb_300_T_0.220_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 5000 | 0 of 500 (0.0%) | 0 |
| last | 1.764e+08 | 16 of 500 (3.2%) | 4 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/hand5/two_species_sweep/equal/Kb_300_T_0.220`
* topology: `/scratch/sroy85/Github/dna/large_crystal/hand5/two_species_sweep/equal/Kb_300_T_0.220/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input`): backend = CUDA, interaction_type = PHB, steps = 1500000000, dt = 0.0005, thermostat = john, T = 0.220, rcut = 2.0, patchyAlpha = 0.12, Ka = 300, Kb = 300
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/two_species_sweep/equal/Kb_300_T_0.220/mc_relaxed.dat` (step 5000)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/two_species_sweep/equal/Kb_300_T_0.220/final_conf.dat` (step 1.764e+08, file last written 2026-10-08 05:31; the run may have continued since)

## Regenerate

```
python hclear2/render_clear2.py run two_species_sweep-equal-Kb_300_T_0.220
```
