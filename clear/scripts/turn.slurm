#!/bin/bash
#SBATCH -q private
#SBATCH -p general
#SBATCH --job-name=phb_turn
#SBATCH -c 4
#SBATCH --mem=24G
#SBATCH -t 4:00:00
#SBATCH -o /scratch/sroy85/Github/dna/large_crystal/PHB_visuals_2026-10-23/logs/turn_%j.out
#SBATCH -e /scratch/sroy85/Github/dna/large_crystal/PHB_visuals_2026-10-23/logs/turn_%j.err
export TMPDIR=${SLURM_TMPDIR:-/tmp}
cd /scratch/sroy85/Github/dna/large_crystal/hand5/final_report
for n in 2sp_3H3L_T0.140 2sp_5L1H_T0.140 2sp_highT_3H3L_T0.170 4sp_ww_T0.140 seed_S128_T0.140_r2 seed_S256_T0.140_r1 crystal_Kb300_T0.100; do
  /home/sroy85/miniconda3/bin/python3 make_visuals.py turn $n
done
