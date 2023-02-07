from Game.Game import Game
from Game.CO import BaseCO, COAdder
from Agent import HumanAgent, DoNothingAgent, AIAgent, RandomAgent
from AWEnv_Gym import AWEnv_Gym
from Game.Unit import UnitLibrary, standard_units
from Game.Terrain import TerrainLibrary, standard_terrain
from SelfplayCallback import SelfplayCallback
from util import linear_schedule

from stable_baselines3.ppo.ppo import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback

from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.evaluation import evaluate_policy
from sb3_contrib.common.maskable.utils import get_action_masks
from sb3_contrib.common.envs import InvalidActionEnvDiscrete
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback

from stable_baselines3.common.policies import ActorCriticPolicy, ActorCriticCnnPolicy
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

from CustomModel import CustomActorCriticPolicy, CustomFeatureExtractor

import random

env_config = {
    "map": "Maps/simple_build_capture.json",
    "max_episode_steps": 10000,
    "render_mode": None,
    "seed": None,
    'agent_player': 'B',
    'co_cls': {'O': COAdder, 'B': COAdder},
    # 'opponent_list': current_opponents
    'opponent_list': [AIAgent(MaskablePPO.load("opponents/model_2", n_steps=0), deterministic=True)]
}
eval_env = make_vec_env(
    env_id=AWEnv_Gym.selfplay_env,
    n_envs=1,
    env_kwargs={'env_config': env_config},
    monitor_dir="Eval_Monitor"
)

episode_rewards_for_opponent, episode_lengths_for_opponent = evaluate_policy(
    MaskablePPO.load("opponents/model_4", n_steps=0),
    eval_env,
    n_eval_episodes=10,
    deterministic=True,
    return_episode_rewards=True,
)

print("Rewards:", episode_rewards_for_opponent)
print("Lengths:", episode_lengths_for_opponent)