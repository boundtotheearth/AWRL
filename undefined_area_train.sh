#!/bin/bash
  
#SBATCH --job-name=testtrain
#SBATCH --gpus=a100:1
#SBATCH --partition=medium
#SBATCH --time=03:00:00

hostname
export PATH="/home/f/farnah/miniconda3/bin:$PATH"
source activate AWRL_env
#conda activate AWRL_env

python train.py \
--n-iters=100 \
--map-name="Maps/Undefined_Area.json" \
--save-path="ppo_undefined_area" \
--load-opponents='opponents' \
--lr=0.0003 \
--n-steps=1024 \
--batch-size=128 \
--max-steps=10000 \
--max-eval-steps=10000 \
--n-eval-episodes=10 \
--n-envs=10 \
--n-eval-envs=10 \
--eval-freq=8 \
--reward-threshold=1.1 \
--ent-coef=1e-3