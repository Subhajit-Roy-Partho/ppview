# hclear2: best-yield run of each study, assembled structure solid / rest translucent (ballstick)

Same image format as `clear2/` (opaque = molecules in an intact tetrahedron, 12% opacity otherwise). Code: `render_clear2.py`.

Yield = intact tetrahedra (4-cliques of the molecule bond graph) per molecule of the **last** configuration (ideal crystal 0.358), computed by `clear/scripts/yield_scan.py` over all 921 final configurations. For each study the run with the highest yield is shown (the best temperature / replicate of that study); studies whose best run reaches >= 0.25 tetrahedra per molecule contribute every system, the others contribute their single best run, plus the best replicate of each small seed (S8, S16, S32, S64). Runs marked `[pre-formed crystal start]` started as a crystal, and melting/anneal runs start from an already grown structure, so their yield is not assembly from scratch. Step counts differ between runs; see each run's README.

| run folder | study / run | T | tetrahedra per molecule | six-valent | largest cluster |
|---|---|---|---|---|---|
| `stiffness_sweep-weak_strong-Kb_300_T_0.070` | hand5/stiffness_sweep/weak_strong/Kb_300_T_0.070 (T=0.07) [pre-formed crystal start] | 0.07 | 0.375 | 64% | 84% |
| `seeding_scan-runs-S256_T0.140_r2` | hand5/seeding_scan/runs/S256_T0.140_r2 (T=0.140) | 0.140 | 0.358 | 53% | 98% |
| `pd-melting-M1-M1_ramp_K1_heat_r2` | phase_diagram/melting/M1/M1_ramp_K1_heat_r2 (T=0.07167) | 0.07167 | 0.344 | 50% | 99% |
| `seeding_scan-runs-KA_S128_T0.140_Ka100_a0.10` | hand5/seeding_scan/runs/KA_S128_T0.140_Ka100_a0.10 (T=0.140) | 0.140 | 0.340 | 48% | 98% |
| `seeding_scan-runs-KA_S128_T0.140_Ka30_a0.10` | hand5/seeding_scan/runs/KA_S128_T0.140_Ka30_a0.10 (T=0.140) | 0.140 | 0.340 | 47% | 98% |
| `seeding_scan-runs-S192_T0.140_r1` | hand5/seeding_scan/runs/S192_T0.140_r1 (T=0.140) | 0.140 | 0.340 | 48% | 97% |
| `seeding_scan-runs-KA_S128_T0.140_Ka10_a0.10` | hand5/seeding_scan/runs/KA_S128_T0.140_Ka10_a0.10 (T=0.140) | 0.140 | 0.338 | 46% | 98% |
| `seeding_scan-runs-KA_S128_T0.140_Ka10_a0.12` | hand5/seeding_scan/runs/KA_S128_T0.140_Ka10_a0.12 (T=0.140) | 0.140 | 0.330 | 42% | 100% |
| `seeding_scan-runs-S128_T0.145_r1` | hand5/seeding_scan/runs/S128_T0.145_r1 (T=0.145) | 0.145 | 0.330 | 51% | 93% |
| `seeding_scan-runs-KA_S128_T0.140_Ka100_a0.12` | hand5/seeding_scan/runs/KA_S128_T0.140_Ka100_a0.12 (T=0.140) | 0.140 | 0.322 | 41% | 99% |
| `seeding_scan-runs-KA_S128_T0.140_Ka1000_a0.10` | hand5/seeding_scan/runs/KA_S128_T0.140_Ka1000_a0.10 (T=0.140) | 0.140 | 0.310 | 42% | 97% |
| `seeding_scan-runs-KA_S128_T0.140_Ka1000_a0.12` | hand5/seeding_scan/runs/KA_S128_T0.140_Ka1000_a0.12 (T=0.140) | 0.140 | 0.310 | 40% | 98% |
| `seeding_scan-runs-KA_S128_T0.140_Ka300_a0.12` | hand5/seeding_scan/runs/KA_S128_T0.140_Ka300_a0.12 (T=0.140) | 0.140 | 0.302 | 38% | 99% |
| `seeding_scan-runs-KA_S128_T0.140_Ka30_a0.12` | hand5/seeding_scan/runs/KA_S128_T0.140_Ka30_a0.12 (T=0.140) | 0.140 | 0.296 | 40% | 99% |
| `pd-replicates-R2-S256_T0.140_rep1` | phase_diagram/replicates/R2/S256_T0.140_rep1 (T=0.14) | 0.14 | 0.296 | 42% | 86% |
| `seeding_scan-runs-S32_T0.140` | hand5/seeding_scan/runs/S32_T0.140 (T=0.140) | 0.140 | 0.290 | 34% | 96% |
| `window_scan-runs-Q_T0.140_a` | hand5/window_scan/runs/Q_T0.140_a (T=0.140) | 0.140 | 0.286 | 33% | 94% |
| `pd-extend-4sp_ww_T0.140_cont` | phase_diagram/extend/4sp_ww_T0.140_cont (T=0.14) | 0.14 | 0.286 | 44% | 98% |
| `preconnected_K300_large-weak_weak-Kb_300_T_0.140` | hand5/preconnected_K300_large/weak_weak/Kb_300_T_0.140 (T=0.140) | 0.140 | 0.282 | 44% | 96% |
| `pd-replicates-R2-S192_T0.140_rep1` | phase_diagram/replicates/R2/S192_T0.140_rep1 (T=0.14) | 0.14 | 0.268 | 34% | 86% |
| `pd-replicates-R5-N500_T0.140_rep3` | phase_diagram/replicates/R5/N500_T0.140_rep3 (T=0.14) | 0.14 | 0.268 | 34% | 93% |
| `seeding_scan-runs-S64_T0.140` | hand5/seeding_scan/runs/S64_T0.140 (T=0.140) | 0.140 | 0.264 | 33% | 92% |
| `seeding_scan-runs-S8_T0.140` | hand5/seeding_scan/runs/S8_T0.140 (T=0.140) | 0.140 | 0.260 | 31% | 93% |
| `pd-replicates-R5-N2000_T0.140_rep4` | phase_diagram/replicates/R5/N2000_T0.140_rep4 (T=0.14) | 0.14 | 0.259 | 34% | 87% |
| `pd-hetero-H3-H3_a0.15_r1` | phase_diagram/hetero/H3/H3_a0.15_r1 (T=0.14) | 0.14 | 0.254 | 32% | 100% |
| `seeding_scan-runs-S16_T0.140` | hand5/seeding_scan/runs/S16_T0.140 (T=0.140) | 0.140 | 0.252 | 26% | 96% |
| `pd-anneal-A5-A5_seedanneal_r2` | phase_diagram/anneal/A5/A5_seedanneal_r2 (T=0.14) | 0.14 | 0.250 | 29% | 90% |
| `pd-hetero-H1-H1_K2_c0t2_T0.138_r1` | phase_diagram/hetero/H1/H1_K2_c0t2_T0.138_r1 (T=0.138) | 0.138 | 0.238 | 30% | 90% |
| `pd-hetero-H4-H4_T0.150_r2` | phase_diagram/hetero/H4/H4_T0.150_r2 (T=0.15) | 0.15 | 0.230 | 34% | 69% |
| `pd-replicates-R3-S128_T0.145_rep1` | phase_diagram/replicates/R3/S128_T0.145_rep1 (T=0.145) | 0.145 | 0.230 | 28% | 69% |
| `pd-melting-M3-M3_L40_T0.14_r2` | phase_diagram/melting/M3/M3_L40_T0.14_r2 (T=0.14) | 0.14 | 0.218 | 21% | 86% |
| `pd-melting-M2-M2_L40_T0.13` | phase_diagram/melting/M2/M2_L40_T0.13 (T=0.13) | 0.13 | 0.212 | 23% | 97% |
| `pd-replicates-R2-S64_T0.140_rep2` | phase_diagram/replicates/R2/S64_T0.140_rep2 (T=0.14) | 0.14 | 0.208 | 22% | 88% |
| `pd-melting-M4-M4_T0.070_r1` | phase_diagram/melting/M4/M4_T0.070_r1 (T=0.07) | 0.07 | 0.206 | 20% | 90% |
| `pd-replicates-R4-U500_T0.140_rep7` | phase_diagram/replicates/R4/U500_T0.140_rep7 (T=0.14) | 0.14 | 0.200 | 16% | 89% |
| `pd-anneal-A3-A3_hold_T0.090_T0.138` | phase_diagram/anneal/A3/A3_hold_T0.090_T0.138 (T=0.138) | 0.138 | 0.196 | 19% | 92% |
| `pd-replicates-R2-S32_T0.140_rep1` | phase_diagram/replicates/R2/S32_T0.140_rep1 (T=0.14) | 0.14 | 0.194 | 15% | 86% |
| `pd-replicates-R2-S16_T0.140_rep1` | phase_diagram/replicates/R2/S16_T0.140_rep1 (T=0.14) | 0.14 | 0.186 | 15% | 76% |
| `pd-anneal-A4-A4_jump_Q130a_T0.145` | phase_diagram/anneal/A4/A4_jump_Q130a_T0.145 (T=0.145) | 0.145 | 0.184 | 15% | 38% |
| `pd-replicates-R2-S8_T0.140_rep4` | phase_diagram/replicates/R2/S8_T0.140_rep4 (T=0.14) | 0.14 | 0.178 | 15% | 93% |
| `pd-unattached-runs-UA_S256_T0.140_r1` | phase_diagram/unattached/runs/UA_S256_T0.140_r1 (T=0.14) | 0.14 | 0.174 | 25% | 66% |
| `seeded_sweep-weak_weak-Kb_1_T_0.060` | hand5/seeded_sweep/weak_weak/Kb_1_T_0.060 (T=0.06) | 0.06 | 0.142 | 12% | 100% |
| `seeded_sweep_s48-weak_weak-Kb_1_T_0.060` | hand5/seeded_sweep_s48/weak_weak/Kb_1_T_0.060 (T=0.06) | 0.06 | 0.142 | 15% | 100% |
| `seeded_sweep_s32-weak_weak-Kb_3_T_0.100` | hand5/seeded_sweep_s32/weak_weak/Kb_3_T_0.100 (T=0.1) | 0.1 | 0.132 | 14% | 100% |
| `preconnected_strength_scan-S50-Kb_300_T_0.100` | hand5/preconnected_strength_scan/S50/Kb_300_T_0.100 (T=0.100) | 0.100 | 0.124 | 11% | 100% |
| `preconnected_seed_sweep-four_species-Kb_300_T_0.140` | hand5/preconnected_seed_sweep/four_species/Kb_300_T_0.140 (T=0.140) | 0.140 | 0.112 | 10% | 100% |
| `pd-anneal-SM-SM_smoke_T0.138` | phase_diagram/anneal/SM/SM_smoke_T0.138 (T=0.138) | 0.138 | 0.104 | 8% | 100% |
| `pd-anneal-A1-A1_cool_R5e8_r2` | phase_diagram/anneal/A1/A1_cool_R5e8_r2 (T=0.13) | 0.13 | 0.088 | 5% | 90% |
| `decisive_equalK-sym_150_150-Kb_300_T_0.078` | hand5/decisive_equalK/sym_150_150/Kb_300_T_0.078 (T=0.078) | 0.078 | 0.086 | 6% | 100% |
| `pd-hetero-H2-H2_5L1H_T0.144_r1` | phase_diagram/hetero/H2/H2_5L1H_T0.144_r1 (T=0.144) | 0.144 | 0.064 | 13% | 99% |
| `two_species_preconnected-3H3L-Kb_300_T_0.140` | hand5/two_species_preconnected/3H3L/Kb_300_T_0.140 (T=0.140) | 0.140 | 0.060 | 13% | 100% |
| `pd-anneal-A2-A2_cycle_n1_r2` | phase_diagram/anneal/A2/A2_cycle_n1_r2 (T=0.145) | 0.145 | 0.044 | 1% | 9% |
| `two_species_sweep-equal-Kb_300_T_0.220` | hand5/two_species_sweep/equal/Kb_300_T_0.220 (T=0.220) | 0.220 | 0.008 | 17% | 100% |
