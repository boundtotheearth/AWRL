#!/bin/bash
  
#SBATCH --job-name=testtrain
#SBATCH --gpus=a100:1
#SBATCH --partition=long
#SBATCH --time=07:00:00

hostname
export PATH="/home/f/farnah/miniconda3/bin:$PATH"
source activate AWRL_env
#conda activate AWRL_env

python train.py --total-timesteps=100000 \
--map-name="Maps/Undefined_Area.json" \
--n-steps=128 \
--batch-size=512 \
--max-steps=10000 \
--max-eval-steps=10000 \
--n-eval-episodes=60 \
--n-envs=30 \
--n-eval-envs=30