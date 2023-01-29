conda run --live-stream -n AWRL_env python train.py \
--map-name="Maps/simple_build_capture.json" \
--load-opponents="opponents" \
--from-checkpoint="ppo_simple/current_model" \
--n-iters=500 \
--n-steps=64 \
--n-eval-episodes=10 \
--eval-freq=1 \
--n-envs=20 \
--n-eval-envs=10 \
--max-steps=1000 \
--max-eval-steps=2000 \
--reward-threshold=1.1 \
--ent-coef=1e-3 \
--lr=0.0001