#!/bin/bash
#SBATCH -q private
#SBATCH -p general
#SBATCH --job-name=phb_video2
#SBATCH --array=0-7
#SBATCH -c 16
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH -t 6:00:00
#SBATCH -o /scratch/sroy85/Github/dna/large_crystal/videos/slurm2_%A_%a.out
#SBATCH -e /scratch/sroy85/Github/dna/large_crystal/videos/slurm2_%A_%a.err

export TMPDIR=${SLURM_TMPDIR:-/tmp}
python3 -c "import matplotlib, imageio_ffmpeg" 2>/dev/null || pip install --quiet --user matplotlib imageio imageio-ffmpeg
python3 /scratch/sroy85/Github/dna/large_crystal/videos/make_phb_videos.py batch2 $SLURM_ARRAY_TASK_ID
