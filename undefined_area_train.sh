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
--n-steps=1024 \
--batch-size=128 \
--max-steps=10000 \
--max-eval-steps=10000 \
--n-eval-episodes=10 \
--n-envs=5 \
--n-eval-envs=5 \
--eval-freq=2048