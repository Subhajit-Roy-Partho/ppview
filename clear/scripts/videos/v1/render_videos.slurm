#!/bin/bash
#SBATCH -q private
#SBATCH -p general
#SBATCH --job-name=phb_video
#SBATCH --array=0-2
#SBATCH -c 8
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH -t 6:00:00
#SBATCH -o /scratch/sroy85/Github/dna/large_crystal/videos/slurm_%A_%a.out
#SBATCH -e /scratch/sroy85/Github/dna/large_crystal/videos/slurm_%A_%a.err

export TMPDIR=${SLURM_TMPDIR:-/tmp}
python3 -c "import matplotlib, imageio_ffmpeg" 2>/dev/null || pip install --quiet --user matplotlib imageio imageio-ffmpeg
python3 /scratch/sroy85/Github/dna/large_crystal/videos/make_phb_videos.py $SLURM_ARRAY_TASK_ID
