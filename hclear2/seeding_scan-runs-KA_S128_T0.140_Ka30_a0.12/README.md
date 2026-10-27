# seeding_scan-runs-KA_S128_T0.140_Ka30_a0.12

**hand5/seeding_scan/runs/KA_S128_T0.140_Ka30_a0.12 (T=0.140)**  
Series: Best temperature of its system

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `seeding_scan-runs-KA_S128_T0.140_Ka30_a0.12_initial_ballstick.png` | starting configuration |
| `seeding_scan-runs-KA_S128_T0.140_Ka30_a0.12_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 5000 | 119 of 500 (23.8%) | 43 |
| last | 3.403e+09 | 426 of 500 (85.2%) | 151 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/KA_S128_T0.140_Ka30_a0.12`
* topology: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/KA_S128_T0.140_Ka30_a0.12/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 1908005000, dt = 0.0005, thermostat = john, T = 0.140, rcut = 2.0, patchyAlpha = 0.12, Ka = 30, Kb = 300, seed = 62605
* staged protocol (`stages.txt`: temperature, steps): T=0.140 x 2,000,000,000; T=0.140 x 3,000,000,000
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/KA_S128_T0.140_Ka30_a0.12/mc_relaxed.dat` (step 5000)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/seeding_scan/runs/KA_S128_T0.140_Ka30_a0.12/final_conf.dat` (step 3.403e+09, file last written 2026-10-26 18:27; the run may have continued since)

## Regenerate

```
python hclear2/render_clear2.py run seeding_scan-runs-KA_S128_T0.140_Ka30_a0.12
```
