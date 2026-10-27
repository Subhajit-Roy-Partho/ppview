# pd-replicates-R5-N500_T0.140_rep3

**phase_diagram/replicates/R5/N500_T0.140_rep3 (T=0.14)**  
Series: Best temperature of its system

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Arms bind cores through complementary patches (colours c and -c). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders: no title, legend, axes or periodic box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration | model |
|---|---|---|
| `pd-replicates-R5-N500_T0.140_rep3_initial_ball.png` | starting configuration | ppview ball model: cores and arm beads as spheres |
| `pd-replicates-R5-N500_T0.140_rep3_initial_ballstick.png` | starting configuration | ball-and-stick: core balls, arm joint balls joined by sticks |
| `pd-replicates-R5-N500_T0.140_rep3_final_ball.png` | last configuration | ppview ball model: cores and arm beads as spheres |
| `pd-replicates-R5-N500_T0.140_rep3_final_ballstick.png` | last configuration | ball-and-stick: core balls, arm joint balls joined by sticks |

Colours: cores are grey; arm beads/sticks are slate; each patch on a core is coloured by its interaction colour id, and a complementary pair (c, -c) shares one colour, so two bonded cores show a matching coloured patch where they touch. Hue is keyed on |c| mod 500; the darker variant marks |c| >= 500 (the strong channels).

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/replicates/R5/N500_T0.140_rep3`
* topology: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/replicates/R5/N500_T0.140_rep3/topology.phb`
* molecules: 500; box 40 x 40 x 40
* parameters (from `input_stage`): backend = CUDA, interaction_type = PHB, steps = 1343005000, dt = 0.0005, thermostat = john, T = 0.14, rcut = 2.0, patchyAlpha = 0.1, Ka = 300, Kb = 300, seed = 30266626
* staged protocol (`stages.txt`: temperature, steps): T=0.14 x 2,000,000,000
* run metadata (`meta.json`): `{"topology": "/scratch/sroy85/Github/dna/large_crystal/phase_diagram/replicates/staging/N500_T0.140_rep3_t0.phb", "conf": "/scratch/sroy85/Github/dna/large_crystal/phase_diagram/replicates/staging/N500_T0.140_rep3_mc.dat", "stages": [[0.14, 2000000000]], "alpha": 0.1, "ka": 300, "kb": 300, "dt": 0.0005, "seed": 30260056, "core_weak": 1.0, "tip_weak": 1.0, "n_patches_rewritten": 36, "study": "R5", "run": "N500_T0.140_rep3", "K": 2, "T": 0.14, "N_molecules": 500, "box": 40.0, "replicate_rng": 20261079, "purpose": "R5 finite-size N=500", "priority": "P2", "parent": "crystal-ball-seed"}`
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/replicates/R5/N500_T0.140_rep3/mc_relaxed.dat` (step 5000; the configuration the MD started from, after the short MC relaxation where one was run)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/phase_diagram/replicates/R5/N500_T0.140_rep3/final_conf.dat` (step 9.7e+08, file last written 2026-10-26 18:29; the run may have continued since)

## Structure at the two configurations

Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `clear/scripts/cluster_labels.py`.

| | step | largest cluster | clusters | mean valence (max 6) | six-valent molecules | intact tetrahedra per molecule |
|---|---|---|---|---|---|---|
| start | 5000 | 25.0% | 1 | 1.17 | 10.8% | 0.078 |
| last | 9.7e+08 | 94.0% | 4 | 4.14 | 33.6% | 0.262 |

(ideal crystal: 0.358 tetrahedra per molecule, six-valent 100%)

## Regenerate

```
python hclear/render_clear.py run pd-replicates-R5-N500_T0.140_rep3
```
or directly: `python render_phb.py --top <topology> --conf <conf> --out img.png --width 3200 --height 2400 --model ball|ballstick`.
