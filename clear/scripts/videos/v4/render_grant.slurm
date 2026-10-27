#!/bin/bash
#SBATCH -q private
#SBATCH -p general
#SBATCH --job-name=phb_grantfig
#SBATCH --array=0-40%12
#SBATCH -c 4
#SBATCH --mem=16G
#SBATCH -t 3:00:00
#SBATCH -o /scratch/sroy85/Github/dna/large_crystal/videos/v4/logs/grant_%A_%a.out
#SBATCH -e /scratch/sroy85/Github/dna/large_crystal/videos/v4/logs/grant_%A_%a.err
export TMPDIR=${SLURM_TMPDIR:-/tmp}
cd /scratch/sroy85/Github/dna/large_crystal/videos/v4
/home/sroy85/miniconda3/bin/python3 grant_frames.py $SLURM_ARRAY_TASK_ID
