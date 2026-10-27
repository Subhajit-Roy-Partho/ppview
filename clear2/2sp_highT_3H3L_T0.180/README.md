# 2sp_highT_3H3L_T0.180

**2-species 3H3L, T=0.180, 32-molecule seed**  
Series: 2-species, higher T

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `2sp_highT_3H3L_T0.180_initial_ballstick.png` | starting configuration |
| `2sp_highT_3H3L_T0.180_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 5000 | 0 of 500 (0.0%) | 0 |
| last | 2e+09 | 36 of 500 (7.2%) | 9 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/TS_3H3L_T0.180`
* topology: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/TS_3H3L_T0.180/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 124005000, dt = 0.0005, thermostat = john, T = 0.180, rcut = 2.0, patchyAlpha = 0.12, Ka = 300, Kb = 300, seed = 60393
* staged protocol (`stages.txt`: temperature, steps): T=0.180 x 2,000,000,000
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/TS_3H3L_T0.180/mc_relaxed.dat` (step 5000)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/TS_3H3L_T0.180/final_conf.dat` (step 2e+09, file last written 2026-10-22 11:44; the run may have continued since)

## Regenerate

```
python clear2/render_clear2.py run 2sp_highT_3H3L_T0.180
```
