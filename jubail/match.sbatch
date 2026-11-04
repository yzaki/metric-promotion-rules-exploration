#!/bin/bash
#SBATCH -J career_match
#SBATCH -p bigmem
#SBATCH --mem=480G
#SBATCH -c 16
#SBATCH -t 06:00:00
#SBATCH -o match_%j.log
cd /scratch/naa9497/citation_targets
echo "start $(date)"
venv/bin/python -u match_career.py
gzip -f career_start.tsv
echo "done $(date)"
