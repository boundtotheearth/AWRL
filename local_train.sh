conda run --live-stream -n AWRL_env python train.py \
--map-name="Maps/simple_build_capture.json" \
--total-timesteps=100000 \
--n-steps=32 \
--n-eval-episodes=10 \
--eval-freq=512 \
--n-envs=30 \
--n-eval-envs=10 \
--max-steps=10000 \
--max-eval-steps=10000