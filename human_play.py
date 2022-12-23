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

# agents = {
#     'O': HumanAgent(BaseCO()),
#     'B': HumanAgent(BaseCO())
# }

def game_generator():
    possible_cos = [{
        'O': BaseCO(),
        'B': BaseCO()
    }, {
        'B': BaseCO(),
        'O': BaseCO()
    }]

    cos = random.choice(possible_cos)

    unit_library = UnitLibrary(standard_units)
    terrain_library = TerrainLibrary(list(cos.keys()), standard_terrain)

    game = Game.load_map(
        map_path="Maps/simple_build.json",
        players_co=cos
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

env_config = {
    "game_generator": game_generator,
    "max_episode_steps": 1000,
    "render_mode": 'text',
    "seed": None,
    "agent_player": "O",
    "opponents": {"B": HumanAgent()}
}

env = make_vec_env(AWEnv_Gym.selfplay_env, n_envs=1, env_kwargs={'env_config': env_config})
observation = env.reset()

env.render(mode='text')

# model = MaskablePPO.load("ppo_simple/best_model")
model = MaskablePPO.load("ppo_simple_build")
# test_agent = RandomAgent()
test_agent = AIAgent(model)

while True:
    action_masks = get_action_masks(env)
    # observation = {key: observation[0] for key, observation in observation.items()}
    # observation = observation[0]
    action = test_agent.get_action(observation, action_masks[0])

    observation, reward, done, info = env.step(action)

    if done[0]:
        print("Done", reward)
        break
