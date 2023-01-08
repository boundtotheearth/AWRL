import argparse
import os
from datetime import datetime

from Game.Game import Game
from Game.CO import BaseCO
from Agent import AIAgent, RandomAgent
from AWEnv_Gym import AWEnv_Gym
from SelfplayCallback import SelfplayCallback
from util import linear_schedule

from stable_baselines3.common.env_util import make_vec_env

from sb3_contrib import MaskablePPO

from CustomModel import CustomFeatureExtractor

parser = argparse.ArgumentParser(
    prog="Training Script",
    description="AWRL Training Script using Stable Baselines3"
)

parser.add_argument("--map-name", type=str, default=None)
parser.add_argument("--from-checkpoint", type=str, default=None)
parser.add_argument("--load-opponents", type=str, default=None)
parser.add_argument("--total-timesteps", type=int, default=100000)
parser.add_argument("--n-steps", type=int, default=128)
parser.add_argument("--batch-size", type=int, default=64)
parser.add_argument("--n-eval-episodes", type=int, default=200)
parser.add_argument("--save-path", type=str, default="ppo_simple")
parser.add_argument("--eval-freq", type=int, default=512)
parser.add_argument("--reward-threshold", type=float, default=0.9)
parser.add_argument("--n-envs", type=int, default=20)
parser.add_argument("--n-eval-envs", type=int, default=20)
parser.add_argument("--max-steps", type=int, default=4000)
parser.add_argument("--max-eval-steps", type=int, default=2000)
parser.add_argument("--lr", type=float, default=1e-3)
parser.add_argument("--n-epochs", type=int, default=10)

args = parser.parse_args()

print(f"Running with args: {args}")

current_opponents = [RandomAgent()]
if args.load_opponents:
    print("Loading opponents...")
    opponent_models = [os.path.join(args.load_opponents, f).replace(".zip", "") for f in os.listdir(args.load_opponents) if os.path.isfile(os.path.join(args.load_opponents, f)) and ".zip" in f]
    opponents = [AIAgent(MaskablePPO.load(model)) for model in opponent_models]
    current_opponents.extend(opponents)
    print(f"Loaded {len(opponents)} opponents: {opponent_models}")

env_config = {
    "map": args.map_name,
    "max_episode_steps": args.max_steps,
    "render_mode": None,
    "seed": None,
    'agent_player': 'random',
    'opponent_list': current_opponents
}
env = make_vec_env(AWEnv_Gym.selfplay_env, n_envs=args.n_envs, env_kwargs={'env_config': env_config})

eval_env_config = {
    "map": args.map_name,
    "max_episode_steps": args.max_eval_steps,
    "render_mode": None,
    "seed": None,
    'agent_player': 'random',
    'opponent_list': current_opponents
}
eval_env = make_vec_env(AWEnv_Gym.selfplay_env, n_envs=args.n_eval_envs, env_kwargs={'env_config': eval_env_config})
selfplay_eval_callback = SelfplayCallback(
    eval_env=eval_env,
    n_eval_episodes=args.n_eval_episodes,
    best_model_save_path=args.save_path,
    eval_freq=args.eval_freq,
    reward_threshold=args.reward_threshold,
    selfplay_opponents=current_opponents
)

policy_kwargs = dict(
    features_extractor_class=CustomFeatureExtractor,
    features_extractor_kwargs=dict(features_dim=128),
)

if args.from_checkpoint:
    print("Loading from checkpoint")
    model = MaskablePPO.load(args.from_checkpoint, env=env)
else:
    print("Train from scratch")
    model = MaskablePPO(
        policy='MultiInputPolicy', 
        env=env, 
        verbose=2, 
        n_steps=args.n_steps, 
        batch_size=args.batch_size,
        learning_rate=args.lr,
        n_epochs=args.n_epochs,
        policy_kwargs=policy_kwargs
    )

obs = env.reset()
print("Training started at", datetime.now().strftime("%H:%M:%S"))
model.learn(total_timesteps=args.total_timesteps, callback=selfplay_eval_callback, progress_bar=True)

final_save_path = os.path.join(args.save_path, "final_model")
model.save(final_save_path)
print(f"TRAINING DONE. Final model saved to {final_save_path}")