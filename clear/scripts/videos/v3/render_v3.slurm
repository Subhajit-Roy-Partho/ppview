#!/bin/bash
#SBATCH -q private
#SBATCH -p general
#SBATCH --job-name=phb_vid_v3
#SBATCH --array=0-40%8
#SBATCH -c 16
#SBATCH --mem=32G
#SBATCH -t 8:00:00
#SBATCH -o /scratch/sroy85/Github/dna/large_crystal/videos/v3/logs/%A_%a.out
#SBATCH -e /scratch/sroy85/Github/dna/large_crystal/videos/v3/logs/%A_%a.err
# v3 re-render: all REG entries, complete first..last frames, species_cluster + crystal end-hold.
# CPU only. Usage: sbatch render_v3.slurm [COLOR_MODE]; default species_cluster.
export TMPDIR=${SLURM_TMPDIR:-/tmp}
cd /scratch/sroy85/Github/dna/large_crystal/videos/v3
MODE=${1:-species_cluster}
/home/sroy85/miniconda3/bin/python3 make_videos_v3.py $SLURM_ARRAY_TASK_ID --color-mode $MODE --procs 16
