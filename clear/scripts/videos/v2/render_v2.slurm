#!/bin/bash
#SBATCH -q private
#SBATCH -p general
#SBATCH --job-name=phb_vid_v2
#SBATCH --array=0-40%12
#SBATCH -c 8
#SBATCH --mem=24G
#SBATCH -t 4:00:00
#SBATCH -o /scratch/sroy85/Github/dna/large_crystal/videos/v2/logs/%A_%a.out
#SBATCH -e /scratch/sroy85/Github/dna/large_crystal/videos/v2/logs/%A_%a.err
export TMPDIR=${SLURM_TMPDIR:-/tmp}
cd /scratch/sroy85/Github/dna/large_crystal/hand5/final_report
/home/sroy85/miniconda3/bin/python3 make_videos.py $SLURM_ARRAY_TASK_ID --procs 8
