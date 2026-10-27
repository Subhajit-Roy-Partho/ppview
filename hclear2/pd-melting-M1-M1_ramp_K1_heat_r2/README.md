# pd-melting-M1-M1_ramp_K1_heat_r2

**phase_diagram/melting/M1/M1_ramp_K1_heat_r2 (T=0.07167)**  
Series: best of study phase_diagram/melting/M1

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders in the ball-and-stick model (core balls, arm joint balls joined by sticks): no title, legend, axes or box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration |
|---|---|
| `pd-melting-M1-M1_ramp_K1_heat_r2_initial_ballstick.png` | starting configuration |
| `pd-melting-M1-M1_ramp_K1_heat_r2_final_ballstick.png` | last configuration |

**Opacity encodes assembly.** A molecule is drawn opaque if it belongs to at least one intact tetrahedron (four mutually bonded molecules, the crystal motif); every other molecule is drawn at 12% opacity. Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`. Cores are grey, arms slate, patches coloured by interaction colour.

| | step | molecules in tetrahedra (opaque) | intact tetrahedra |
|---|---|---|---|
| start | 1.5e+09 | 447 of 500 (89.4%) | 172 |
| last | 2.244e+09 | 446 of 500 (89.2%) | 170 |

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M1/M1_ramp_K1_heat_r2`
* topology: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M1/M1_ramp_K1_heat_r2/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 34005000, dt = 0.0005, thermostat = john, T = 0.07167, rcut = 2.0, patchyAlpha = 0.1, Ka = 300, Kb = 300, seed = 43262
* staged protocol (`stages.txt`: temperature, steps): T=0.05833 x 150,000,000; T=0.06167 x 150,000,000; T=0.065 x 150,000,000; T=0.06833 x 150,000,000; T=0.07167 x 150,000,000; T=0.075 x 150,000,000; T=0.07667 x 300,000,000; T=0.07833 x 150,000,000; T=0.08 x 300,000,000; T=0.08167 x 150,000,000; T=0.08333 x 300,000,000; T=0.085 x 150,000,000; T=0.08667 x 300,000,000; T=0.08833 x 150,000,000; T=0.09167 x 150,000,000; T=0.095 x 150,000,000; T=0.09833 x 150,000,000; T=0.10167 x 150,000,000; T=0.105 x 150,000,000; T=0.10833 x 150,000,000
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M1/M1_ramp_K1_heat_r2/mc_relaxed.dat` (step 1.5e+09)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/melting/M1/M1_ramp_K1_heat_r2/final_conf.dat` (step 2.244e+09, file last written 2026-10-26 18:37; the run may have continued since)

## Regenerate

```
python hclear2/render_clear2.py run pd-melting-M1-M1_ramp_K1_heat_r2
```
