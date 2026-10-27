# pd-anneal-A1-A1_cool_R5e8_r2

**phase_diagram/anneal/A1/A1_cool_R5e8_r2 (T=0.13)**  
Series: best of study phase_diagram/anneal/A1

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `pd-anneal-A1-A1_cool_R5e8_r2_initial_ballstick.png` | starting configuration |
| `pd-anneal-A1-A1_cool_R5e8_r2_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 9.263e+08 | 190 of 500 (38.0%) | 56 |
| last | 1.944e+09 | 160 of 500 (32.0%) | 43 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A1/A1_cool_R5e8_r2`
* topology: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A1/A1_cool_R5e8_r2/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 134300000, dt = 0.0005, thermostat = john, T = 0.13, rcut = 2.0, patchyAlpha = 0.1, Ka = 300, Kb = 300, seed = 50021
* staged protocol (`stages.txt`: temperature, steps): T=0.19 x 300,000,000; T=0.19 x 20,000,000; T=0.1875 x 20,000,000; T=0.185 x 20,000,000; T=0.1825 x 20,000,000; T=0.18 x 20,000,000; T=0.1775 x 20,000,000; T=0.175 x 20,000,000; T=0.1725 x 20,000,000; T=0.17 x 20,000,000; T=0.1675 x 20,000,000; T=0.165 x 20,000,000; T=0.1625 x 20,000,000; T=0.16 x 20,000,000; T=0.1575 x 20,000,000; T=0.155 x 20,000,000; T=0.1525 x 20,000,000; T=0.15 x 20,000,000; T=0.1475 x 20,000,000; T=0.145 x 20,000,000; T=0.1425 x 20,000,000; T=0.14 x 20,000,000; T=0.1375 x 20,000,000; T=0.135 x 20,000,000; T=0.1325 x 20,000,000; T=0.13 x 20,000,000; T=0.13 x 300,000,000
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A1/A1_cool_R5e8_r2/mc_relaxed.dat` (step 9.263e+08)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/anneal/A1/A1_cool_R5e8_r2/final_conf.dat` (step 1.944e+09, file last written 2026-10-26 18:37; the run may have continued since)

## Regenerate

```
python hclear2/render_clear2.py run pd-anneal-A1-A1_cool_R5e8_r2
```
