#!/bin/bash -l
#SBATCH -q private
#SBATCH -p general
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH -J clear_render
#SBATCH -o /scratch/sroy85/Github/ppview/clear/render_all_%j.out
# CPU only (numpy rasteriser): renders every run in manifest.json, ball + ballstick, initial + final.
cd /scratch/sroy85/Github/ppview/clear
/home/sroy85/miniconda3/bin/python3 render_clear.py all -j 6
