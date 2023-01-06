#!/bin/bash
  
#SBATCH --job-name=testtrain
#SBATCH --gpus=a100:1
#SBATCH --partition=medium
#SBATCH --time=03:00:00

hostname
export PATH="/home/f/farnah/miniconda3/bin:$PATH"
source activate AWRL_env
#conda activate AWRL_env

python train.py --total-timesteps=200000 \
--map-name="Maps/Mind_Trap.json" \
--n-steps=512 \
--batch-size=64 \
--max-steps=1000 \
--max-eval-steps=1000 \
