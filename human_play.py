from sb3_contrib import MaskablePPO
from Agent import AIAgent, HumanAgent, RandomAgent
from Game.CO import BaseCO, COAdder
from AWEnv_Gym import AWEnv_Gym
from Game.Unit import UnitLibrary, standard_units
from Game.Terrain import TerrainLibrary, standard_terrain
from Game.Game import Game
from SelfplayWrapper import SelfplayWrapper

import random

from stable_baselines3.ppo.ppo import PPO
from stable_baselines3.common.env_util import make_vec_env

from sb3_contrib.common.maskable.utils import get_action_masks

env_config = {
    "map": "Maps/simple_build_capture.json",
    "max_episode_steps": 10000,
    "render_mode": 'text',
    "seed": None,
    "agent_player": "B",
    'co_cls': {'O': COAdder, 'B': COAdder},
    "opponent_list": [AIAgent(MaskablePPO.load("opponents/model_6"), deterministic=True)],
    "strict": False
}

env = make_vec_env(AWEnv_Gym.selfplay_env, n_envs=1, env_kwargs={'env_config': env_config})
observation = env.reset()

env.render(mode='text')

model = MaskablePPO.load("opponents/model_6", n_steps=0)
# test_agent = RandomAgent()
test_agent = AIAgent(model, deterministic=True)

episode_reward = 0
while True:
    action_masks = get_action_masks(env)
    # observation = {key: observation[0] for key, observation in observation.items()}
    # observation = observation[0]
    action = test_agent.get_action(observation, action_masks[0])

    observation, reward, done, info = env.step(action)
    episode_reward += reward
    print(reward)

    if done[0]:
        print("Done", reward)
        break
    input("Turn ended")
print(episode_reward)
