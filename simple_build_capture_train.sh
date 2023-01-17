#!/bin/bash
  
#SBATCH --job-name=testtrain
#SBATCH --gpus=a100:1
#SBATCH --partition=long
#SBATCH --time=3-00:00:00

hostname
export PATH="/home/f/farnah/miniconda3/bin:$PATH"
source activate AWRL_env
#conda activate AWRL_env

python train.py \
--map-name="Maps/simple_build_capture.json" \
--load-opponents="opponents" \
--n-iters=100 \
--n-steps=32 \
--n-eval-episodes=10 \
--eval-freq=8 \
--n-envs=30 \
--n-eval-envs=10 \
--max-steps=2000 \
--max-eval-steps=2000 \
--reward-threshold=1.1 \
--ent-coef=1e-3