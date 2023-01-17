from gym import Env, spaces
from gym.wrappers import TimeLimit, FlattenObservation
from SelfplayWrapper import SelfplayWrapper

import pprint
import random
import numpy as np
import math
from collections import OrderedDict

from Game.Game import Game
from Game.CO import BaseCO
from Game.Action import Action, ActionEnd, ActionMove, ActionMoveCombineLoad, ActionDirectAttack, ActionIndirectAttack, ActionCapture, ActionBuild, ActionRepair, ActionUnload
from Agent import Agent
from Game.Terrain import Property, standard_terrain
from Game.Unit import standard_units

class AWEnv_Gym(Env):
    metadata = {"render_modes": ["none", "text", "raw"]}

    @classmethod
    def flat_env(cls, env_config):
        return FlattenObservation(
            TimeLimit(
                cls(env_config), 
                max_episode_steps=env_config.get("max_episode_steps")
            )
        )
    
    @classmethod
    def selfplay_flat_env(cls, env_config):
        return TimeLimit(
                SelfplayWrapper(
                    FlattenObservation(
                        cls(env_config)
                    ),
                    agent_player=env_config.get("agent_player"),
                    opponents=env_config.get("opponents")
                ),
                max_episode_steps=env_config.get("max_episode_steps")
            )

    @classmethod
    def selfplay_env(cls, env_config):
        return TimeLimit(
                SelfplayWrapper(
                    cls(env_config),
                    agent_player=env_config.get("agent_player"),
                    opponent_list=env_config.get("opponent_list")
                ),
                max_episode_steps=env_config.get("max_episode_steps")
            )

    possible_directions = [(-1, 0), (1, 0), (0, 1), (0, -1)]

    def __init__(self, env_config):
        super().__init__()

        self.env_config = env_config

        self.map = env_config.get('map')
        strict = env_config.get('strict', True)
        self.game = env_config.get('game') or self.generate_game(self.map, strict)
        self.seed(env_config.get('seed', 0))
        self.gamma = env_config.get('gamma', 0.99)

        self.players = self.game.get_players_list()

        self.rows = self.game.map_height
        self.cols = self.game.map_width

        terrain_list = [terrain for terrain in standard_terrain if not issubclass(terrain, Property)]
        property_list = [terrain for terrain in standard_terrain if issubclass(terrain, Property)]

        self.prev_potential = {player: self.calculate_potential(player) for player in self.players}

        self.max_move = 9
        self.max_attack = 8

        self.render_mode = env_config.get("render_mode", 'text')
        self.actions = OrderedDict({
            ActionMoveCombineLoad: (self.rows, self.cols, (2*self.max_move)+1, (2*self.max_move)+1),
            ActionDirectAttack: (self.rows, self.cols, (2*self.max_move)+1, (2*self.max_move)+1, 4),
            ActionIndirectAttack: (self.rows, self.cols, (2*self.max_attack)+1, (2*self.max_attack)+1),
            ActionCapture: (self.rows, self.cols, (2*self.max_move)+1, (2*self.max_move)+1),
            ActionBuild: (self.rows, self.cols, len(standard_units)),
            ActionRepair: (self.rows, self.cols, (2*self.max_move)+1, (2*self.max_move)+1, 4),
            ActionUnload: (self.rows, self.cols, (2*self.max_move)+1, (2*self.max_move)+1, 4, 2),
            ActionEnd: (1,)
        })

        self.action_start_ids = {}
        start_id = 0
        for action_cls in self.actions:
            self.action_start_ids[action_cls] = start_id
            start_id += math.prod(self.actions[action_cls])
        
        # Most algos do not support dict actions, so flatten the action space
        self.total_action_size = sum([math.prod(action_shape) for action_shape in self.actions.values()])
        self.action_space = spaces.Discrete(self.total_action_size)
        self.action_mask = {action_type: np.full(self.actions[action_type], False) for action_type in self.actions}

        self.observation_space = spaces.Dict(OrderedDict({
            "terrain": spaces.Box(low=0, high=1, shape=(len(terrain_list), self.rows, self.cols)), #[0, 1] for each terrain type
            "properties": spaces.Box(low=0, high=20, shape=(3, len(property_list), self.rows, self.cols)), # [0, 20] for each property type, for each player
            "units": spaces.Box(low=0, high=100, shape=(2, len(standard_units), 3, self.rows, self.cols)), # [0, 10] health, [0, 99] fuel, [0, 99] ammo, for each unit type, for each player
            "funds": spaces.Box(low=0, high=999999, shape=(2,)),
        }))

        self.terrain_indices = {terrain_type: i for i, terrain_type in enumerate(terrain_list)}
        self.property_indices = {terrain_type: i for i, terrain_type in enumerate(property_list)}
        self.unit_indices = {unit_type: i for i, unit_type in enumerate(standard_units)}

        self.update_valid_actions()
    
    def generate_game(self, map, strict):
        cos = {
            'O': BaseCO(),
            'B': BaseCO()
        }
        game = Game.load_map(
            map_path=map,
            players_co=cos,
            save_history=False,
            strict=strict
        )
        return game

    def fetch_action(self, action_id):
        action_type = None
        for a_type, a_start_id in self.action_start_ids.items():
            if a_start_id > action_id:
                break
            action_type = a_type

        
        sub_action_id = action_id - self.action_start_ids[action_type]
        action_args = np.unravel_index(sub_action_id, self.actions[action_type])
        return self._valid_actions[action_type][action_args]

    def step(self, action):
        if not isinstance(action, Action):
            # action = self._valid_actions[action]
            action = self.fetch_action(action)

        assert action is not None

        if self.render_mode is not None:
            print(action)
        
        player = self.game.get_current_player()
        winner = self.game.execute_action(action)

        if self.render_mode is not None:
            self.render(self.render_mode)
            print(self.game.state.get_player_stats())

        self.update_valid_actions()

        new_player = self.game.get_current_player()
        observation = self.get_observation(new_player)

        reward = self.calculate_reward(player, winner)
        done = winner is not None
        info = {}

        return observation, reward, done, info

    def get_observation(self, player):
        height = self.rows
        width = self.cols
        players = len(self.players)

        observation = {
            'terrain': np.zeros((len(self.terrain_indices), height, width), dtype=int),
            'properties': np.zeros((players+1, len(self.property_indices), height, width), dtype=int),
            'units': np.zeros((players, len(self.unit_indices), 3, height, width), dtype=int),
            'funds': np.zeros((players), dtype=int)
        }

        get_terrain = self.game.state.get_terrain
        get_property = self.game.state.get_property
        get_unit = self.game.state.get_unit

        for r in range(height):
            for c in range(width):
                position = (r, c)
                terrain = get_terrain(position)
                if not isinstance(terrain, Property):
                    observation['terrain'][self.terrain_indices[type(terrain)], r, c] = 1

                for p in self.players:
                    p_id = 0 if p is player else 1
                    unit = get_unit(position, owner=p)
                    if unit is not None:
                        observation['units'][p_id, self.unit_indices[type(unit)], 0, r, c] = unit.get_display_health()
                        observation['units'][p_id, self.unit_indices[type(unit)], 1, r, c] = unit.fuel
                        observation['units'][p_id, self.unit_indices[type(unit)], 2, r, c] = unit.ammo
                    

                property = get_property(position)
                if property is not None:
                    p_id = 0 if property.owner is player else 2 if property.owner == 'N' else 1
                    observation['properties'][p_id, self.property_indices[type(property)], r, c] = 1
        
        for p in self.players:
            p_id = 0 if p is player else 1
            observation['funds'][p_id] = self.game.state.funds[p]

        return observation
    
    def calculate_reward(self, player, winner):
        reward = -1 / self.env_config.get("max_episode_steps")
        if winner is player:
            reward += 1
        elif winner is not None:
            reward -= 1

        new_potential = self.calculate_potential(player)
        reward += (new_potential - self.prev_potential[player])

        self.prev_potential[player] = new_potential

        return reward
        
    def calculate_potential(self, player):
        player_stats = self.game.state.get_player_stats()
        player_potential = 0
        other_potential = 0
        for other_player, stats in player_stats.items():
            if other_player == player:
                player_potential += stats['army_value']
                player_potential +=  5 * stats['income']
            else:
                other_potential += stats['army_value']
                other_potential += 5 * stats['income']

        potential = player_potential / (player_potential + other_potential)
        return potential

    def action_masks(self):
        action_masks = np.concatenate([self.action_mask[action_type].flatten() for action_type in self.actions])
        return action_masks
    
    def update_valid_actions(self):
        # Construct action masks that match the shapes defined by self.actions
        valid_actions = {action_type: {} for action_type in self.actions}
        for action_array in self.action_mask.values():
            action_array.fill(False)

        current_state = self.game.state
        all_units = current_state.get_all_units()
        current_player = self.game.get_current_player()
        enemy_units = {position: unit for position, unit in all_units.items() if unit.owner != current_player}

        valid_actions[ActionEnd][(0,)] = ActionEnd()
        self.action_mask[ActionEnd][(0,)] = True

        possible_directions = self.possible_directions
        
        for position, unit in all_units.items():
            if unit.owner != current_player or not unit.available:
                continue

            r, c = position

            #Indirect Attack
            if 1 not in unit.range:
                for attack_position_r, attack_position_c in enemy_units:
                    attack_offset_r = attack_position_r - r
                    attack_offset_c = attack_position_c - c

                    attack_offset_id_r = attack_offset_r + self.max_attack
                    attack_offset_id_c = attack_offset_c + self.max_attack

                    indirect_attack_action = ActionIndirectAttack(position, (attack_offset_r, attack_offset_c))
                    if indirect_attack_action.validate(current_state):
                        action_args = (r, c, attack_offset_id_r, attack_offset_id_c)
                        valid_actions[ActionIndirectAttack][action_args] = indirect_attack_action
                        self.action_mask[ActionIndirectAttack][action_args] = True

            for unblocked_position_r, unblocked_position_c in current_state._unblocked_spaces[position]:
                move_offset_r = unblocked_position_r - r
                move_offset_c = unblocked_position_c - c
            
                move_action = ActionMove(unit_position=position, offset=(move_offset_r, move_offset_c))
                if not move_action.validate(current_state):
                    continue

                # Avoid negative indices
                move_id_r = move_offset_r + self.max_move
                move_id_c = move_offset_c + self.max_move
                #Move/Combine/Load
                move_combine_load_action = ActionMoveCombineLoad(move_action=move_action)
                if move_combine_load_action.validate(current_state):
                    action_args = (r, c, move_id_r, move_id_c)
                    valid_actions[ActionMoveCombineLoad][action_args] = move_combine_load_action
                    self.action_mask[ActionMoveCombineLoad][action_args] = True
                
                #Direct Attack
                if 1 in unit.range:
                    for direction_index, direction in enumerate(possible_directions):
                        direct_attack_action = ActionDirectAttack(move_action=move_action, attack_offset=direction)
                        if direct_attack_action.attack_target not in enemy_units:
                            continue

                        if direct_attack_action.validate(current_state):
                            action_args = (r, c, move_id_r, move_id_c, direction_index)
                            valid_actions[ActionDirectAttack][action_args] = direct_attack_action
                            self.action_mask[ActionDirectAttack][action_args] = True
                
                #Capture
                if unit.can_capture:
                    capture_action = ActionCapture(move_action=move_action)
                    if capture_action.validate(current_state):
                        action_args = (r, c, move_id_r, move_id_c)
                        valid_actions[ActionCapture][action_args] = capture_action
                        self.action_mask[ActionCapture][action_args] = True
                        

                #Repair
                if unit.can_repair:
                    for direction_index, direction in enumerate(possible_directions):
                        repair_action = ActionRepair(move_action=move_action, repair_offset=direction)
                        if repair_action.validate(current_state):
                            action_args = (r, c, move_id_r, move_id_c, direction_index)
                            valid_actions[ActionRepair][action_args] = repair_action
                            self.action_mask[ActionRepair][action_args] = True

                #Unload
                for idx in range(len(unit.in_load)):
                    for direction_index, direction in enumerate(possible_directions):
                        unload_action = ActionUnload(move_action=move_action, unload_offset=direction, idx=idx)
                        if unload_action.unload_position in all_units:
                            continue
                        if unload_action.validate(current_state):
                            action_args = (r, c, move_id_r, move_id_c, direction_index, idx)
                            valid_actions[ActionUnload][action_args] = unload_action
                            self.action_mask[ActionUnload][action_args] = True

        for position, property in current_state.get_all_properties(owner=current_player).items(): 
            r, c = position                  
            #Build
            for unit_type in property.buildables:
                idx = self.unit_indices[unit_type]
                build_action = ActionBuild(position, unit_type.code)
                if build_action.validate(current_state):
                    action_args = (r, c, idx)
                    valid_actions[ActionBuild][action_args] = build_action
                    self.action_mask[ActionBuild][action_args] = True

        # Flatten the action masks to match the actual flat action space
        self._valid_actions = valid_actions 

    def reset(self, seed=0, return_info=False, options=None):
        strict = self.env_config.get('strict', True)
        self.game = self.env_config.get('game') or self.generate_game(self.map, strict)
        current_player = self.game.get_current_player()

        self.update_valid_actions()
        return self.get_observation(current_player)
    
    def render(self, mode, **kwargs):
        if mode == "text":
            print(f"Day {self.game.state.current_day}")
            print(f"Player {self.game.get_current_player()}'s turn")
            print(self.game.state)
        elif mode == "raw":
            pp = pprint.PrettyPrinter()
            pp.pprint(self.get_observation())
    
    def seed(self, seed=0):
        random.seed(seed)