# window_Q_T0.140

**melt at T=0.17 then hold T=0.14**  
Series: Melt-quench

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `window_Q_T0.140_initial_ballstick.png` | starting configuration |
| `window_Q_T0.140_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 5000 | 31 of 500 (6.2%) | 10 |
| last | 2.375e+09 | 409 of 500 (81.8%) | 140 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/hand5/window_scan/runs/Q_T0.140_a`
* topology: `/scratch/sroy85/Github/dna/large_crystal/hand5/window_scan/runs/Q_T0.140_a/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 946005000, dt = 0.0005, thermostat = john, T = 0.140, rcut = 2.0, patchyAlpha = 0.1, Ka = 300, Kb = 300, seed = 20285650
* staged protocol (`stages.txt`: temperature, steps): T=0.170 x 10,000,000; T=0.140 x 800,000,000; T=0.140 x 2,200,000,000
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/window_scan/runs/Q_T0.140_a/start_conf.dat` (step 5000)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/window_scan/runs/Q_T0.140_a/final_conf.dat` (step 2.375e+09, file last written 2026-10-26 17:47; the run may have continued since)

## Regenerate

```
python clear2/render_clear2.py run window_Q_T0.140
```
