conda run --live-stream -n AWRL_env python train.py \
--map-name="Maps/simple_build.json" \
--from-checkpoint="ppo_simple/custom_model_test" \
--total-timesteps=100000 \
--n-eval-episodes=100 \
--eval-freq=128 \
--n-envs=20 \
--n-eval-envs=20 \
--max-steps=100 \
--max-eval-steps=50