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
--n-iters=1000 \
--map-name="Maps/Caustic_Finale.json" \
--from-checkpoint="ppo_caustic_finale/current_model" \
--save-path="ppo_caustic_finale" \
--load-opponents='opponents' \
--lr=0.0004 \
--n-steps=1024 \
--batch-size=64 \
--max-steps=10000 \
--max-eval-steps=10000 \
--n-eval-episodes=10 \
--n-envs=10 \
--n-eval-envs=10 \
--eval-freq=8 \
--reward-threshold=1.1 \
--ent-coef=1e-3