# seeded_sweep-weak_weak-Kb_1_T_0.060

**hand5/seeded_sweep/weak_weak/Kb_1_T_0.060 (T=0.06)**  
Series: best of study hand5/seeded_sweep

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `seeded_sweep-weak_weak-Kb_1_T_0.060_initial_ballstick.png` | starting configuration |
| `seeded_sweep-weak_weak-Kb_1_T_0.060_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 5000 | 7 of 500 (1.4%) | 2 |
| last | 4.002e+09 | 221 of 500 (44.2%) | 71 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeded_sweep/weak_weak/Kb_1_T_0.060`
* topology: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeded_sweep/weak_weak/Kb_1_T_0.060/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input`): backend = CUDA, interaction_type = PHB, steps = 1500000000, dt = 0.0005, thermostat = john, T = 0.06, rcut = 2.0, patchyAlpha = 0.1, Ka = 300.0, Kb = 1.0
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeded_sweep/weak_weak/Kb_1_T_0.060/mc_relaxed.dat` (step 5000)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeded_sweep/weak_weak/Kb_1_T_0.060/final_conf.dat` (step 4.002e+09, file last written 2026-10-06 17:46; the run may have continued since)

## Regenerate

```
python hclear2/render_clear2.py run seeded_sweep-weak_weak-Kb_1_T_0.060
```
