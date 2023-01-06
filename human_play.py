from sb3_contrib import MaskablePPO
from Agent import AIAgent, HumanAgent, RandomAgent
from Game.CO import BaseCO
from AWEnv_Gym import AWEnv_Gym
from Game.Unit import UnitLibrary, standard_units
from Game.Terrain import TerrainLibrary, standard_terrain
from Game.Game import Game
from SelfplayWrapper import SelfplayWrapper

import random

from stable_baselines3.ppo.ppo import PPO
from stable_baselines3.common.env_util import make_vec_env

from sb3_contrib.common.maskable.utils import get_action_masks

def game_generator():
    cos = {
        'O': BaseCO(),
        'B': BaseCO()
    }

    game = Game.load_map(
        map_path="Maps/simple_build.json",
        players_co=cos,
        save_history=False
    )

    return game

env_config = {
    "game_generator": game_generator,
    "max_episode_steps": 10000,
    "render_mode": 'text',
    "seed": None,
    "agent_player": "random",
    "opponent_list": [AIAgent(MaskablePPO.load("ppo_simple/model_1"))]
}

env = make_vec_env(AWEnv_Gym.selfplay_env, n_envs=1, env_kwargs={'env_config': env_config})
observation = env.reset()
print(env.get_attr('opponents'))

env.render(mode='text')

model = MaskablePPO.load("Models/simple_build/best_model")
# model = MaskablePPO.load("ppo_simple_build")
# test_agent = RandomAgent()
test_agent = AIAgent(model)

while True:
    action_masks = get_action_masks(env)
    # observation = {key: observation[0] for key, observation in observation.items()}
    # observation = observation[0]
    action = test_agent.get_action(observation, action_masks[0])
    print(action)

    observation, reward, done, info = env.step(action)

    if done[0]:
        print("Done", reward)
        break
