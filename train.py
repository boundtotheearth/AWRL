import argparse
import os
from datetime import datetime
from copy import deepcopy
import numpy as np

from Game.Game import Game
from Game.CO import BaseCO
from Agent import AIAgent, RandomAgent
from AWEnv_Gym import AWEnv_Gym
from SelfplayCallback import SelfplayCallback
from util import linear_schedule

from stable_baselines3.common.env_util import make_vec_env

from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.evaluation import evaluate_policy

from CustomModel import CustomFeatureExtractor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Training Script",
        description="AWRL Training Script using Stable Baselines3"
    )

    parser.add_argument("--map-name", type=str, default=None)
    parser.add_argument("--from-checkpoint", type=str, default=None)
    parser.add_argument("--load-opponents", type=str, default=None)
    parser.add_argument("--n-iters", type=int, default=100)
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
    parser.add_argument("--lr", type=float, default=0.0003)
    parser.add_argument("--n-epochs", type=int, default=10)
    parser.add_argument("--ent-coef", type=float, default=0.0)
    parser.add_argument("--gamma", type=float, default=0.99)

    args = parser.parse_args()

    print(f"Running with args: {args}")

    current_opponents = [RandomAgent()]
    if args.load_opponents:
        print("Loading opponents...")
        opponent_models = [os.path.join(args.load_opponents, f).replace(".zip", "") for f in os.listdir(args.load_opponents) if os.path.isfile(os.path.join(args.load_opponents, f)) and ".zip" in f]
        opponents = [AIAgent(MaskablePPO.load(model, n_steps=0), name=model) for model in opponent_models]
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
    env = make_vec_env(
        env_id=AWEnv_Gym.selfplay_env,
        n_envs=args.n_envs,
        monitor_dir="Train_Monitor",
        env_kwargs={'env_config': env_config}
    )

    eval_env_config = {
        "map": args.map_name,
        "max_episode_steps": args.max_eval_steps,
        "render_mode": None,
        "seed": None,
        'agent_player': 'random'
    }
    # eval_env = make_vec_env(AWEnv_Gym.selfplay_env, n_envs=args.n_eval_envs, env_kwargs={'env_config': eval_env_config})
    selfplay_eval_callback = SelfplayCallback(
        eval_env_config=eval_env_config,
        n_eval_envs=args.n_eval_envs,
        n_eval_episodes_per_opponent=args.n_eval_episodes,
        best_model_save_path=args.save_path,
        monitor_dir="Eval_Monitor",
        eval_freq=args.eval_freq,
        reward_threshold=args.reward_threshold,
        selfplay_opponents=current_opponents,
    )

    # Defined custom CNN feature extractor
    policy_kwargs = dict(
        features_extractor_class=CustomFeatureExtractor,
        features_extractor_kwargs=dict(features_dim=128),
    )

    # Initialize model
    if args.from_checkpoint:
        print("Loading from checkpoint")
        model = MaskablePPO.load(
            args.from_checkpoint,
            env=env,
            n_steps=args.n_steps,
            batch_size=args.batch_size,
            n_epochs=args.n_epochs,
            ent_coef=args.ent_coef,
            gamma=args.gamma
        )
    else:
        print("Train from scratch")
        model = MaskablePPO(
            policy='MultiInputPolicy', 
            env=env, 
            verbose=1, 
            n_steps=args.n_steps, 
            batch_size=args.batch_size,
            n_epochs=args.n_epochs,
            policy_kwargs=policy_kwargs,
            ent_coef=args.ent_coef,
            gamma=args.gamma
        )

    env.reset()
    print("Training started at", datetime.now().strftime("%H:%M:%S"))
    for iter in range(1, args.n_iters + 1):
        print(f"Iteration {iter} started at", datetime.now().strftime("%H:%M:%S"))
        #Adjust learning rate
        model.learning_rate = ((args.n_iters + 1 - iter) / (args.n_iters + 1)) * args.lr
        model._setup_lr_schedule()

        model.learn(total_timesteps=args.n_steps * args.n_envs, reset_num_timesteps=False, progress_bar=True)

        model_save_path = os.path.join(args.save_path, "current_model")
        model.save(model_save_path)

        model.logger.dump()
        
        if iter % args.eval_freq == 0:
            print("Evaluation started at", datetime.now().strftime("%H:%M:%S"))

            model.logger.record("league/league_size", len(current_opponents))

            episode_rewards = []
            episode_lengths = []
            defeated = False
            for opponent in current_opponents:
                print(f"Evaluation against {opponent} started at", datetime.now().strftime("%H:%M:%S"))
                env_config = deepcopy(eval_env_config)
                env_config['opponent_list'] = [opponent]
                eval_env = make_vec_env(
                    env_id=AWEnv_Gym.selfplay_env,
                    n_envs=args.n_eval_envs,
                    env_kwargs={'env_config': env_config},
                    monitor_dir="Eval_Monitor"
                )
                
                episode_rewards_for_opponent, episode_lengths_for_opponent = evaluate_policy(
                    model,
                    eval_env,
                    n_eval_episodes=args.n_eval_episodes,
                    deterministic=True,
                    return_episode_rewards=True,
                )
                mean_reward_for_opponent, std_reward_for_opponent = np.mean(episode_rewards_for_opponent), np.std(episode_rewards_for_opponent)
                mean_ep_length_for_opponent, std_ep_length_for_opponent = np.mean(episode_lengths_for_opponent), np.std(episode_lengths_for_opponent)
                
                model.logger.record(f"{opponent}/ep_reward", f"{mean_reward_for_opponent} +/- {std_reward_for_opponent}")
                model.logger.record(f"{opponent}/ep_length", f"{mean_ep_length_for_opponent} +/- {std_ep_length_for_opponent}")

                episode_rewards.extend(episode_rewards_for_opponent)
                episode_lengths.extend(episode_lengths_for_opponent)

                if mean_reward_for_opponent < args.reward_threshold:
                    print(f"Model was defeated by {opponent}")
                    defeated = True

            mean_reward, std_reward = np.mean(episode_rewards), np.std(episode_rewards)
            mean_ep_length, std_ep_length = np.mean(episode_lengths), np.std(episode_lengths)

            model.logger.record("eval/mean_reward", float(mean_reward))
            model.logger.record("eval/mean_ep_length", mean_ep_length)
            
            if not defeated:
                print("All previous models defeated! Adding a new opponent!")
                new_model_id = len(current_opponents)
                new_model_name = os.path.join(args.load_opponents, f"model_{new_model_id}")
                model.save(new_model_name)
                new_model = MaskablePPO.load(new_model_name, n_steps=0) # n_steps=0 to avoid allocating buffer
                current_opponents.append(AIAgent(new_model, name=new_model_name, deterministic=True))
                best_mean_reward = -np.inf
                
            model.logger.dump()
            print("Evaluation completed at", datetime.now().strftime("%H:%M:%S"))

    print("Training done. Saving model...")
    final_save_path = os.path.join(args.save_path, "final_model")
    model.save(final_save_path)
    print(f"Final model saved to {final_save_path}")