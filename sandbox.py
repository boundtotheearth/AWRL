from Game.Game import Game
from Game.CO import BaseCO
from Agent import HumanAgent, DoNothingAgent, AIAgent, RandomAgent
from AWEnv_Gym import AWEnv_Gym
from Game.Unit import UnitLibrary, standard_units
from Game.Terrain import TerrainLibrary, standard_terrain

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

def game_generator():
    # possible_cos = [{
    #     'O': BaseCO(),
    #     'B': BaseCO()
    # }, {
    #     'B': BaseCO(),
    #     'O': BaseCO()
    # }]

    # cos = random.choice(possible_cos)

    cos = {
        'O': BaseCO(),
        'B': BaseCO()
    }

    unit_library = UnitLibrary(standard_units)
    terrain_library = TerrainLibrary(list(cos.keys()), standard_terrain)

    game = Game.load_map(
        map_path="Maps/simple_build.json",
        players_co=cos,
        save_history=False
    )

    # possible_terrains = ["PLN", "WOD", "NCT", "MTN"]
    # for r, row in enumerate(game.state.terrain):
    #     for c, terrain in enumerate(row):
    #         chosen_terrain_code = random.choice(possible_terrains)
    #         game.state.terrain[r][c] = terrain_library.create(chosen_terrain_code)


    # possible_positions = [i for i in range(36)]
    # random_positions = [(index // 6, index % 6) for index in random.sample(possible_positions, k=4)]

    # game.state.units = {
    #     random_positions[0]: unit_library.create("INF", 'O'),
    #     random_positions[1]: unit_library.create("INF", 'O'),
    #     random_positions[2]: unit_library.create("INF", 'B'),
    #     random_positions[3]: unit_library.create("INF", 'B')
    # }

    return game

def linear_schedule(initial_value: float):
    def func(progress_remaining: float) -> float:
        return progress_remaining * initial_value
    return func

agent = AIAgent(None)

env_config = {
    "game_generator": game_generator,
    "max_episode_steps": 4000,
    "render_mode": None,
    "seed": None,
    'agent_player': 'O',
    'opponents': {'B': RandomAgent()}
}
env = make_vec_env(AWEnv_Gym.selfplay_env, n_envs=20, env_kwargs={'env_config': env_config})

eval_env_config = {
    "game_generator": game_generator,
    "max_episode_steps": 2000,
    "render_mode": None,
    "seed": None,
    'agent_player': 'O',
    'opponents': {'B': RandomAgent()}
}
eval_env = make_vec_env(AWEnv_Gym.selfplay_env, n_envs=20, env_kwargs={'env_config': eval_env_config})
eval_callback = MaskableEvalCallback(eval_env=eval_env, n_eval_episodes=200, best_model_save_path="ppo_simple", eval_freq=512)
# eval_callback = EvalCallback(eval_env=eval_env, n_eval_episodes=200, best_model_save_path="ppo_simple", eval_freq=512)

# model = MaskablePPO("MlpPolicy", env, verbose=1, n_steps=512, learning_rate=2.5e-4)
# model = MaskablePPO.load("ppo_simple/ppo_land_6x6", env, learning_rate=2.5e-4)

# model = PPO(CustomActorCriticPolicy, env, verbose=1, n_steps=128, learning_rate=2.5e-4)
policy_kwargs = dict(
    features_extractor_class=CustomFeatureExtractor,
    features_extractor_kwargs=dict(features_dim=128),
)
model = MaskablePPO('MultiInputPolicy', env, verbose=1, n_steps=128, learning_rate=linear_schedule(1e-3), policy_kwargs=policy_kwargs)
agent.model = model

obs = env.reset()
model.learn(total_timesteps=100000, callback=eval_callback, progress_bar=True)

model.save(f"ppo_simple/custom_model_test")
print("TRAINING DONE")
