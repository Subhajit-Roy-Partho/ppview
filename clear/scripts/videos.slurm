#!/bin/bash
#SBATCH -q private
#SBATCH -p general
#SBATCH --job-name=phb_vis_vid
#SBATCH --array=0-37%10
#SBATCH -c 8
#SBATCH --mem=24G
#SBATCH -t 5:00:00
#SBATCH -o /scratch/sroy85/Github/dna/large_crystal/PHB_visuals_2026-10-23/logs/vid_%A_%a.out
#SBATCH -e /scratch/sroy85/Github/dna/large_crystal/PHB_visuals_2026-10-23/logs/vid_%A_%a.err
export TMPDIR=${SLURM_TMPDIR:-/tmp}
cd /scratch/sroy85/Github/dna/large_crystal/hand5/final_report
/home/sroy85/miniconda3/bin/python3 make_visuals.py vid $SLURM_ARRAY_TASK_ID
