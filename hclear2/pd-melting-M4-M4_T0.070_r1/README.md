# pd-melting-M4-M4_T0.070_r1

**phase_diagram/melting/M4/M4_T0.070_r1 (T=0.07)**  
Series: best of study phase_diagram/melting/M4

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `pd-melting-M4-M4_T0.070_r1_initial_ballstick.png` | starting configuration |
| `pd-melting-M4-M4_T0.070_r1_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 0 | 119 of 500 (23.8%) | 43 |
| last | 1.042e+09 | 312 of 500 (62.4%) | 99 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M4/M4_T0.070_r1`
* topology: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M4/M4_T0.070_r1/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 471500000, dt = 0.0005, thermostat = john, T = 0.07, rcut = 2.0, patchyAlpha = 0.1, Ka = 300, Kb = 300, seed = 34386
* staged protocol (`stages.txt`: temperature, steps): T=0.07 x 1,500,000,000
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M4/M4_T0.070_r1/mc_relaxed.dat` (step 0)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M4/M4_T0.070_r1/final_conf.dat` (step 1.042e+09, file last written 2026-10-26 18:42; the run may have continued since)

## Regenerate

```
python hclear2/render_clear2.py run pd-melting-M4-M4_T0.070_r1
```
