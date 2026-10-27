#!/bin/bash
#SBATCH -q private
#SBATCH -p general
#SBATCH --job-name=phb_vid_v4
#SBATCH --array=0-40%8
#SBATCH -c 16
#SBATCH --mem=32G
#SBATCH -t 8:00:00
#SBATCH -o /scratch/sroy85/Github/dna/large_crystal/videos/v4/logs/%A_%a.out
#SBATCH -e /scratch/sroy85/Github/dna/large_crystal/videos/v4/logs/%A_%a.err
# v4: complete first..last frames, species colours in-cluster + grey outside,
# crystal end-hold, fps 8 (slower). CPU only.
export TMPDIR=${SLURM_TMPDIR:-/tmp}
cd /scratch/sroy85/Github/dna/large_crystal/videos/v4
MODE=${1:-species_cluster}
/home/sroy85/miniconda3/bin/python3 make_videos_v4.py $SLURM_ARRAY_TASK_ID --color-mode $MODE --procs 16
