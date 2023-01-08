#!/bin/bash
  
#SBATCH --job-name=testtrain
#SBATCH --gpus=titan:1
#SBATCH --partition=long
#SBATCH --time=07:00:00

hostname
export PATH="/home/f/farnah/miniconda3/bin:$PATH"
source activate AWRL_env
#conda activate AWRL_env

python train.py --total-timesteps=100000 \
--map-name="Maps/Undefined_Area.json" \
--n-steps=1024 \
--batch-size=1024 \
--max-steps=2000 \
--max-eval-steps=2000 \
--n-eval-episodes=50