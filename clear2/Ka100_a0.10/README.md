# Ka100_a0.10

**Ka=100, alpha=0.10**  
Series: Ka x alpha study (S128, T=0.14)

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `Ka100_a0.10_initial_ballstick.png` | starting configuration |
| `Ka100_a0.10_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 5000 | 119 of 500 (23.8%) | 43 |
| last | 3.306e+09 | 439 of 500 (87.8%) | 168 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/KA_S128_T0.140_Ka100_a0.10`
* topology: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/KA_S128_T0.140_Ka100_a0.10/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 1801005000, dt = 0.0005, thermostat = john, T = 0.140, rcut = 2.0, patchyAlpha = 0.10, Ka = 100, Kb = 300, seed = 63264
* staged protocol (`stages.txt`: temperature, steps): T=0.140 x 2,000,000,000; T=0.140 x 3,000,000,000
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/KA_S128_T0.140_Ka100_a0.10/mc_relaxed.dat` (step 5000)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/KA_S128_T0.140_Ka100_a0.10/final_conf.dat` (step 3.306e+09, file last written 2026-10-26 17:48; the run may have continued since)

## Regenerate

```
python clear2/render_clear2.py run Ka100_a0.10
```
