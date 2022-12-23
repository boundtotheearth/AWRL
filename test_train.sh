#!/bin/bash

#SBATCH --job-name=testtrain
#SBATCH --gpus=titan:1
#SBATCH --partition=long
#SBATCH --time=07:00:00

hostname
export PATH="/home/f/farnah/miniconda3/bin:$PATH"
source activate AWRL_env
#conda activate AWRL_env
conda info
which python
conda list
python sandbox.py
