#!/bin/bash
#SBATCH -q private
#SBATCH -p general
#SBATCH --job-name=phb_stills
#SBATCH -c 16
#SBATCH --mem=48G
#SBATCH -t 6:00:00
#SBATCH -o /scratch/sroy85/Github/dna/large_crystal/PHB_visuals_2026-10-23/logs/stills_%j.out
#SBATCH -e /scratch/sroy85/Github/dna/large_crystal/PHB_visuals_2026-10-23/logs/stills_%j.err
export TMPDIR=${SLURM_TMPDIR:-/tmp}
cd /scratch/sroy85/Github/dna/large_crystal/hand5/final_report
export PROCS=16
/home/sroy85/miniconda3/bin/python3 make_visuals.py mgl
/home/sroy85/miniconda3/bin/python3 make_visuals.py img
