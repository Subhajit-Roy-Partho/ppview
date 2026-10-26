# crystal_Kb1_T0.100

**pre-formed crystal, weak-weak K=2, Kb=1, T=0.10**  
Series: Pre-formed crystal (2048 molecules)

PHB system: patchy helix-bundle molecules, each an icosahedral core (radius 1, with coloured interaction patches) carrying three helix arms of five beads (radius 0.1). Arms bind cores through complementary patches (colours c and -c). Simulated with oxDNA (`interaction_type = PHB`, CUDA, MD).

## Images

Pure configuration renders: no title, legend, axes or periodic box; white background; isometric orthographic view of the whole configuration; 3200x2400 px.

| file | configuration | model |
|---|---|---|
| `crystal_Kb1_T0.100_initial_ball.png` | starting configuration | ppview ball model: cores and arm beads as spheres |
| `crystal_Kb1_T0.100_initial_ballstick.png` | starting configuration | ball-and-stick: core balls, arm joint balls joined by sticks |
| `crystal_Kb1_T0.100_final_ball.png` | last configuration | ppview ball model: cores and arm beads as spheres |
| `crystal_Kb1_T0.100_final_ballstick.png` | last configuration | ball-and-stick: core balls, arm joint balls joined by sticks |

Colours: cores are grey; arm beads/sticks are slate; each patch on a core is coloured by its interaction colour id, and a complementary pair (c, -c) shares one colour, so two bonded cores show a matching coloured patch where they touch. Hue is keyed on |c| mod 500; the darker variant marks |c| >= 500 (the strong channels).

## Simulation

* run directory: `/scratch/sroy85/Github/dna/large_crystal/hand5/stiffness_sweep/weak_weak/Kb_1_T_0.100`
* topology: `/scratch/sroy85/Github/dna/large_crystal/hand5/stiffness_sweep/base_weak_weak.phb`
* molecules: 2048; box 168 x 168 x 168
* parameters (from `input`): backend = CUDA, interaction_type = PHB, steps = 1500000000, dt = 0.0005, thermostat = john, T = 0.1, rcut = 2.0, patchyAlpha = 0.1, Ka = 300.0, Kb = 1.0
* starting configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/stiffness_sweep/weak_weak/Kb_1_T_0.100/mc_relaxed.dat` (step 5000; the configuration the MD started from, after the short MC relaxation where one was run)
* last configuration: `/scratch/sroy85/Github/dna/large_crystal/hand5/stiffness_sweep/weak_weak/Kb_1_T_0.100/final_conf.dat` (step 1.5e+09, file last written 2026-10-25 08:00; the run may have continued since)

## Structure at the two configurations

Bonds: complementary patches on different molecules with patch distance < 0.3 (minimum image), as in `scripts/cluster_labels.py`.

| | step | largest cluster | clusters | mean valence (max 6) | six-valent molecules | intact tetrahedra per molecule |
|---|---|---|---|---|---|---|
| start | 5000 | 70.9% | 11 | 4.62 | 61.7% | 0.358 |
| last | 1.5e+09 | 73.0% | 28 | 4.79 | 63.4% | 0.372 |

(ideal crystal: 0.358 tetrahedra per molecule, six-valent 100%)

## Regenerate

```
python clear/render_clear.py run crystal_Kb1_T0.100
```
or directly: `python render_phb.py --top <topology> --conf <conf> --out img.png --width 3200 --height 2400 --model ball|ballstick`.
