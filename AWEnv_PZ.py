import gym
from gym import spaces

import copy
import pprint
import random

from Game.Action import ActionEnd, ActionMove, ActionAttack, ActionCapture, ActionBuild, ActionRepair, ActionUnload

from pettingzoo.utils.env import AECEnv
from pettingzoo.utils import agent_selector
from pettingzoo.utils.wrappers import BaseWrapper

class AWEnv_PZ(AECEnv):
    metadata = {"render_modes": ["none", "text", "raw"]}

    def __init__(self, env_config):
        super().__init__()

        self.game = env_config.get('game')
        self.game_template = copy.deepcopy(self.game)
        self.seed(env_config.get('seed', 0))

        self.agents = self.game.players
        self.possible_agents = self.agents[:]

        player_list = self.game.get_players_list()
        terrain_list = self.game.get_terrain_list()
        property_list = self.game.get_property_list()
        unit_list = self.game.get_unit_list()

        rows = self.game.map_height
        cols = self.game.map_width

        self.observation_spaces = spaces.Dict({
            agent: spaces.Dict({
                "terrain": spaces.Dict({terrain.code: spaces.Box(low=0, high=1, shape=(rows, cols)) for terrain in terrain_list}), #[0, 1] for each terrain type
                "properties": spaces.Dict({
                    "self": spaces.Dict({property.code: spaces.Box(low=0, high=20, shape=(rows, cols)) for property in property_list}),
                    "other": spaces.Dict({property.code: spaces.Box(low=0, high=20, shape=(rows, cols)) for property in property_list}),
                }), # [0, 20] for each property type, for each player
                "units": spaces.Dict({
                    "self": spaces.Dict({unit.code: spaces.Box(low=0, high=100, shape=(3, rows, cols)) for unit in unit_list}),
                    "other": spaces.Dict({unit.code: spaces.Box(low=0, high=100, shape=(3, rows, cols)) for unit in unit_list}),
                }), # [0, 10] health, [0, 99] fuel, [0, 99] ammo, for each unit type, for each player
                "funds": spaces.Dict({
                    'self': spaces.Box(low=0, high=999999, shape=(1,)),
                    'other': spaces.Box(low=0, high=999999, shape=(1,)),
                })
            })
            for agent in self.agents
        })

        self.rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.dones = {agent: False for agent in self.agents}
        self.infos = {agent: None for agent in self.agents}

        self._agent_selector = agent_selector(self.agents)
        self.agent_selection = self._agent_selector.reset()

        self.render_mode = env_config.get("render_mode", 'text')

        self.actions = {
            0: ActionEnd,
            1: ActionMove,
            2: ActionAttack,
            3: ActionCapture,
            4: ActionBuild,
            5: ActionRepair,
            6: ActionUnload
        }

        self.action_spaces = {agent: spaces.MultiDiscrete([len(self.actions), rows * cols, rows * cols]) for agent in self.agents} # Action type, source index, target index

    def observation_space(self, agent):
        return self.observation_spaces[agent]

    def action_space(self, agent):
        return self.action_spaces[agent]

    def observe(self, agent):
        return self.game.get_observation(agent)

    def step(self, action):
        if self.terminations[self.agent_selection] or self.truncations[self.agent_selection]:
            self._was_dead_step(action)
            return

        action_type = self.actions[action[0]]
        action_source = (action[1] // self.rows, action[1] % self.rows)
        action_target = (action[2] // self.rows, action[2] % self.rows)

        if action_type is ActionEnd:
            action = ActionEnd()
        elif action_type is ActionMove:
            row_direction = 1 if action_target[0] - action_source[0] >= 0 else -1
            row_directions = [(row_direction, 0) for row in range(action_source[0], action_target[0] + row_direction, row_direction)]
            col_direction = 1 if action_target[1] - action_source[1] >= 0 else -1
            col_directions = [(0, col_direction) for col in range(action_source[1], action_target[1] + col_direction, col_direction)]
            directions = row_directions + col_directions
            action = ActionMove(action_source, directions, False)
        elif action_type is ActionAttack:
            row_direction = 1 if action_target[0] - action_source[0] >= 0 else -1
            row_directions = [(row_direction, 0) for row in range(action_source[0], action_target[0] + row_direction, row_direction)]
            col_direction = 1 if action_target[1] - action_source[1] >= 0 else -1
            col_directions = [(0, col_direction) for col in range(action_source[1], action_target[1] + col_direction, col_direction)]
            directions = row_directions + col_directions
            action = ActionAttack(action_source, directions)
        elif action_type is ActionCapture:
            action = ActionCapture(action_source)
        elif action_type is ActionBuild:
            action = ActionBuild(action_source, "INF")
        elif action_type is ActionRepair:
            row_direction = 1 if action_target[0] - action_source[0] >= 0 else -1
            col_direction = 1 if action_target[1] - action_source[1] >= 0 else -1
            action = ActionRepair(action_source, (row_direction, col_direction))
        elif action_type is ActionUnload:
            row_direction = 1 if action_target[0] - action_source[0] >= 0 else -1
            col_direction = 1 if action_target[1] - action_source[1] >= 0 else -1
            action = ActionUnload(action_source, 0, (row_direction, col_direction))

        winner = self.game.execute_action(action)
        
        self.rewards = {agent: 1 if winner is agent else 0 for agent in self.agents}
        self.terminations = {agent: winner is not None for agent in self.agents}
        self.dones = {agent: winner is not None for agent in self.agents}

        self._accumulate_rewards()

        if self.render_mode is not None:
            self.render(self.render_mode)

        self.agent_selection = self.game.state.get_current_player()

    def reset(self, seed=0, return_info=False, options=None):
        self.game = copy.deepcopy(self.game_template)
        self.agents = self.possible_agents[:]
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.dones = {agent: False for agent in self.agents}
        self.infos = {agent: None for agent in self.agents}
        self.agent_selection = self.agents[0]
    
    def render(self, mode, **kwargs):
        if mode == "text":
            print(self.game.state)
        elif mode == "raw":
            pp = pprint.PrettyPrinter()
            pp.pprint(self.game.get_observation())
    
    def seed(self, seed=0):
        random.seed(seed)

    #Override to use done instead of terminate/truncate, for compatibility with rlllib
    def last(self, observe=True):
        observation, reward, terminate, truncate, info = super().last(observe)
        return observation, reward, terminate or truncate, info

# class TinyMoveEnv(AWEnv):
#     def step(self, action):
#         super().step(action)

#         self.rewards['O'] = 1 if self.observe('O')['units']['self']['INF'][0][0, 4] > 0 else 0
#         self.terminations['O'] = self.rewards['O'] == 1