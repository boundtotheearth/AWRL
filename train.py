import argparse
import os
from datetime import datetime
from copy import deepcopy
import numpy as np

from Game.Game import Game
from Game.CO import BaseCO, COAdder
from Agent import AIAgent, RandomAgent
from AWEnv_Gym import AWEnv_Gym
from SelfplayCallback import SelfplayCallback
from util import linear_schedule, exponential_schedule

from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.utils import get_schedule_fn

from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.evaluation import evaluate_policy

from CustomModel import CustomFeatureExtractor, CustomActorCriticPolicy

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
    parser.add_argument("--eval-freq", type=int, default=1)
    parser.add_argument("--reward-threshold", type=float, default=0.9)
    parser.add_argument("--reward-type", type=str, default="binary")
    parser.add_argument("--n-envs", type=int, default=20)
    parser.add_argument("--n-eval-envs", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=4000)
    parser.add_argument("--max-eval-steps", type=int, default=2000)
    parser.add_argument("--lr", type=float, default=0.0003)
    parser.add_argument("--lr-decay-rate", type=float, default=1)
    parser.add_argument("--clip-range", type=float, default=0.2)
    parser.add_argument("--clip-range-decay-rate", type=float, default=0)
    parser.add_argument("--n-epochs", type=int, default=10)
    parser.add_argument("--ent-coef", type=float, default=0.0)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--gamma-max", type=float, default=1)
    parser.add_argument("--gamma-decay-rate", type=float, default=0)

    args = parser.parse_args()

    print(f"Running with args: {args}")

    current_opponents = [RandomAgent()]
    if args.load_opponents:
        print("Loading opponents...")
        opponent_models = sorted([os.path.join(args.load_opponents, f).replace(".zip", "") for f in os.listdir(args.load_opponents) if os.path.isfile(os.path.join(args.load_opponents, f)) and ".zip" in f], key=lambda x: int(x.split("_")[1]))
        opponents = [AIAgent(MaskablePPO.load(model, n_steps=0), name=model) for model in opponent_models]
        current_opponents.extend(opponents)
        print(f"Loaded {len(opponents)} opponents: {opponent_models}")

    agent = AIAgent(None)
    env_config = {
        "map": args.map_name,
        "max_episode_steps": args.max_steps,
        "render_mode": None,
        "seed": None,
        'agent_player': 'random',
        'co_cls': {'O': COAdder, 'B': COAdder},
        'opponent_list': current_opponents,
        'reward_type': args.reward_type
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
        'co_cls': {'O': COAdder, 'B': COAdder},
        'reward_type': args.reward_type
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
    # policy_kwargs = dict(
    #     features_extractor_class=CustomFeatureExtractor
    # )

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
            policy=CustomActorCriticPolicy, 
            env=env, 
            verbose=1, 
            n_steps=args.n_steps, 
            batch_size=args.batch_size,
            n_epochs=args.n_epochs,
            ent_coef=args.ent_coef,
            gamma=args.gamma
        )

    agent.model = model
    
    env.reset()
    print("Training started at", datetime.now().strftime("%H:%M:%S"))
    lr_schedule = exponential_schedule(args.lr, args.lr_decay_rate)
    clip_range_schedule = exponential_schedule(args.clip_range, args.clip_range_decay_rate)
    gamma_schedule = exponential_schedule(1 - args.gamma, args.gamma_decay_rate, 1 - args.gamma_max)
    for iter in range(1, args.n_iters + 1):
        print(f"Iteration {iter} started at", datetime.now().strftime("%H:%M:%S"))
        
        progress_remaining = (args.n_iters + 1 - iter) / (args.n_iters + 1)

        #Adjust learning rate
        model.learning_rate = lr_schedule(progress_remaining)
        model.lr_schedule = get_schedule_fn(model.learning_rate)

        #Adjust clip range
        model.clip_range = get_schedule_fn(clip_range_schedule(progress_remaining))

        #Adjust gamma
        model.gamma = 1 - gamma_schedule(progress_remaining)
        model.rollout_buffer.gamma = 1 - gamma_schedule(progress_remaining)
        
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
                for player in ["O", "B"]:
                    print(f"Evaluation against {opponent} with agent as {player} started at", datetime.now().strftime("%H:%M:%S"))
                    env_config = deepcopy(eval_env_config)
                    env_config['opponent_list'] = [opponent]
                    env_config['agent_player'] = player
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
                    
                    model.logger.record(f"{opponent}/{player}/ep_reward", f"{mean_reward_for_opponent} +/- {std_reward_for_opponent}")
                    model.logger.record(f"{opponent}/{player}/ep_length", f"{mean_ep_length_for_opponent} +/- {std_ep_length_for_opponent}")

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