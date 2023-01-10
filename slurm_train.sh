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
--from-checkpoint="ppo_simple/final_model" \
--load-opponents="opponents" \
--map-name="Maps/simple_build.json" \
--n-steps=128 \
--batch-size=64 \
--max-steps=1000 \
--max-eval-steps=1000 \
