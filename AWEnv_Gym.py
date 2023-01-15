import gym
from gym import Env, spaces
from gym.wrappers import TimeLimit, FlattenObservation
from SelfplayWrapper import SelfplayWrapper

import copy
import pprint
import random
import numpy as np
from numpy import ravel_multi_index
import math
from collections import OrderedDict

from Game.Game import Game
from Game.CO import BaseCO
from Game.Action import Action, ActionEnd, ActionMove, ActionMoveCombineLoad, ActionDirectAttack, ActionIndirectAttack, ActionCapture, ActionBuild, ActionRepair, ActionUnload
from Agent import Agent

from enum import Enum

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

        self.player_list = self.game.get_players_list()
        self.terrain_list = self.game.get_terrain_list()
        self.property_list = self.game.get_property_list()
        self.unit_list = self.game.get_unit_list()

        self.rows = self.game.map_height
        self.cols = self.game.map_width

        self.prev_potential = {player: self.calculate_potential(player) for player in self.player_list}

        self.max_move = 9
        self.max_attack = 8

        self.render_mode = env_config.get("render_mode", 'text')
        self.actions = OrderedDict({
            ActionMoveCombineLoad: (self.rows, self.cols, (2*self.max_move)+1, (2*self.max_move)+1),
            ActionDirectAttack: (self.rows, self.cols, (2*self.max_move)+1, (2*self.max_move)+1, 4),
            ActionIndirectAttack: (self.rows, self.cols, (2*self.max_attack)+1, (2*self.max_attack)+1),
            ActionCapture: (self.rows, self.cols, (2*self.max_move)+1, (2*self.max_move)+1),
            ActionBuild: (self.rows, self.cols, len(self.unit_list)),
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
        self.action_mask = np.full((self.total_action_size,), False)

        self.observation_space = spaces.Dict(OrderedDict({
            "terrain": spaces.Box(low=0, high=1, shape=(len(self.terrain_list), self.rows, self.cols)), #[0, 1] for each terrain type
            "properties": spaces.Box(low=0, high=20, shape=(2, len(self.property_list), self.rows, self.cols)), # [0, 20] for each property type, for each player
            "units": spaces.Box(low=0, high=100, shape=(2, len(self.unit_list), 3, self.rows, self.cols)), # [0, 10] health, [0, 99] fuel, [0, 99] ammo, for each unit type, for each player
            "funds": spaces.Box(low=0, high=999999, shape=(2,)),
        }))

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

    # def create_action(self, action_id):
    #     # Extract action type and arguments from action index based on the shapes of actions spaces
    #     action_start_id = 0
    #     for action_type, action_shape in self.actions.items():
    #         action_count = math.prod(action_shape)
    #         action_end_id = action_start_id + action_count
    #         if action_id >= action_start_id and action_id < action_end_id:
    #             action_args = action_id - action_start_id
    #             action = action_type
    #             break
                
    #         action_start_id = action_end_id

    #     # Construct Action object from type and arguments
    #     if action is ActionMoveCombineLoad:
    #         source_r, source_c, offset_id_r, offset_id_c = np.unravel_index(action_args, self.actions[action])
    #         action_source = (source_r, source_c)
    #         action_offset = (offset_id_r - self.max_move, offset_id_c - self.max_move)

    #         action = ActionMoveCombineLoad(action_source, action_offset)
    #     elif action is ActionDirectAttack:
    #         source_r, source_c, move_offset_r, move_offset_c, attack_direction = np.unravel_index(action_args, self.actions[action])
    #         source = (source_r, source_c)
    #         move_offset = (move_offset_r - self.max_move, move_offset_c - self.max_move)
    #         attack_offset = parse_direction(attack_direction)

    #         action = ActionDirectAttack(source, move_offset, attack_offset)
    #     elif action is ActionIndirectAttack:
    #         source_r, source_c, attack_offset_id_r, attack_offset_id_c = np.unravel_index(action_args, self.actions[action])
    #         source = (source_r, source_c)
    #         attack_offset = (attack_offset_id_r - self.max_attack, attack_offset_id_c - self.max_attack)

    #         action = ActionIndirectAttack(source, attack_offset)
    #     elif action is ActionCapture:
    #         source_r, source_c, offset_r, offset_c = np.unravel_index(action_args, self.actions[action])
    #         source = (source_r, source_c)
    #         offset = (offset_r - self.max_move, offset_c - self.max_move)

    #         action = ActionCapture(source, offset)
    #     elif action is ActionBuild:
    #         source_r, source_c, unit_idx = np.unravel_index(action_args, self.actions[action])
    #         source = (source_r, source_c)
    #         unit_code = self.unit_list[unit_idx].code

    #         action = ActionBuild(source, unit_code)
    #     elif action is ActionRepair:
    #         source_r, source_c, move_offset_r, move_offset_c, repair_direction = np.unravel_index(action_args, self.actions[action])
    #         source = (source_r, source_c)
    #         move_offset = (move_offset_r - self.max_move, move_offset_c - self.max_move)
    #         repair_offset = parse_direction(repair_direction)

    #         action = ActionRepair(source, move_offset, repair_offset)
    #     elif action is ActionUnload:
    #         source_r, source_c, move_offset_r, move_offset_c, unload_direction, unit_idx = np.unravel_index(action_args, self.actions[action])
    #         source = (source_r, source_c)
    #         move_offset = (move_offset_r - self.max_move, move_offset_c - self.max_move)
    #         unload_offset = parse_direction(unload_direction)

    #         action = ActionUnload(source, move_offset, unload_offset, unit_idx)
    #     else:
    #         action = ActionEnd()

    #     return action

    def step(self, action):
        if not isinstance(action, Action):
            action = self._valid_actions[action]

        assert action is not None

        if self.render_mode is not None:
            print(action)
            
        winner = self.game.execute_action(action)

        if self.render_mode is not None:
            self.render(self.render_mode)
            print(self.game.state.get_player_stats())

        self.update_valid_actions()
    
        observation = self.game.get_observation(self.game.get_current_player())

        reward = self.calculate_reward(winner)
        done = winner is not None
        info = {}

        return observation, reward, done, info
    
    def calculate_reward(self, winner):
        current_player = self.game.get_current_player()
        reward = 0
        if winner is current_player:
            reward += 100
        elif winner is not None:
            reward -= 100

        new_potential = self.calculate_potential(current_player)
        reward += (new_potential - self.prev_potential[current_player]) / 1000

        self.prev_potential[current_player] = new_potential

        return reward
        
    def calculate_potential(self, player):
        player_stats = self.game.state.get_player_stats()
        potential = 0
        for other_player, stats in player_stats.items():
            if other_player == player:
                potential += stats['army_value']
                potential += stats['income']
            else:
                potential -= stats['army_value']
                potential -= stats['income']
        return potential

    def action_masks(self):
        self.action_mask.fill(False)
        self.action_mask[list(self._valid_actions.keys())] = True
        return self.action_mask
    
    def update_valid_actions(self):
        # Construct action masks that match the shapes defined by self.actions
        valid_actions = {}
        current_state = self.game.state
        all_units = current_state.get_all_units()
        current_player = self.game.get_current_player()
        enemy_units = {position: unit for position, unit in all_units.items() if unit.owner != current_player}

        end_action_id = self.action_start_ids[ActionEnd]
        valid_actions[end_action_id] = ActionEnd()

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
                        sub_action_id = ravel_multi_index((r, c, attack_offset_id_r, attack_offset_id_c), self.actions[ActionIndirectAttack])
                        action_id = self.action_start_ids[ActionIndirectAttack] + sub_action_id
                        valid_actions[action_id] = indirect_attack_action

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
                    sub_action_id = ravel_multi_index((r, c, move_id_r, move_id_c), self.actions[ActionMoveCombineLoad])
                    action_id = self.action_start_ids[ActionMoveCombineLoad] + sub_action_id
                    valid_actions[action_id] = move_combine_load_action
                
                #Direct Attack
                for direction_index, direction in enumerate(possible_directions):
                    direct_attack_action = ActionDirectAttack(move_action=move_action, attack_offset=direction)
                    if direct_attack_action.attack_target not in enemy_units:
                        continue

                    if direct_attack_action.validate(current_state):
                        sub_action_id = ravel_multi_index((r, c, move_id_r, move_id_c, direction_index), self.actions[ActionDirectAttack])
                        action_id = self.action_start_ids[ActionDirectAttack] + sub_action_id
                        valid_actions[action_id] = direct_attack_action

                #Capture
                capture_action = ActionCapture(move_action=move_action)
                if capture_action.validate(current_state):
                    sub_action_id = ravel_multi_index((r, c, move_id_r, move_id_c), self.actions[ActionCapture])
                    action_id = self.action_start_ids[ActionCapture] + sub_action_id
                    valid_actions[action_id] = capture_action

                #Repair
                if unit.can_repair:
                    for direction_index, direction in enumerate(possible_directions):
                        repair_action = ActionRepair(move_action=move_action, repair_offset=direction)
                        if repair_action.validate(current_state):
                            sub_action_id = ravel_multi_index((r, c, move_id_r, move_id_c, direction_index), self.actions[ActionRepair])
                            action_id = self.action_start_ids[ActionRepair] + sub_action_id
                            valid_actions[action_id] = repair_action

                #Unload
                for idx in range(len(unit.in_load)):
                    for direction_index, direction in enumerate(possible_directions):
                        unload_action = ActionUnload(move_action=move_action, unload_offset=direction, idx=idx)
                        if unload_action.unload_position in all_units:
                            continue
                        if unload_action.validate(current_state):
                            sub_action_id = ravel_multi_index((r, c, move_id_r, move_id_c, direction_index, idx), self.actions[ActionUnload])
                            action_id = self.action_start_ids[ActionUnload] + sub_action_id
                            valid_actions[action_id] = unload_action

        for position, property in current_state.get_all_properties(owner=current_player).items(): 
            r, c = position                  
            #Build
            for unit_type in property.buildables:
                idx = self.unit_list.index(unit_type)
                build_action = ActionBuild(position, unit_type.code)
                if build_action.validate(current_state):
                    sub_action_id = ravel_multi_index((r, c, idx), self.actions[ActionBuild])
                    action_id = self.action_start_ids[ActionBuild] + sub_action_id
                    valid_actions[action_id] = build_action

        # Flatten the action masks to match the actual flat action space
        self._valid_actions = valid_actions 

    def reset(self, seed=0, return_info=False, options=None):
        strict = self.env_config.get('strict', True)
        self.game = self.env_config.get('game') or self.generate_game(self.map, strict)
        current_player = self.game.get_current_player()

        self.update_valid_actions()
        return self.game.get_observation(self.game.get_current_player())
    
    def render(self, mode, **kwargs):
        if mode == "text":
            print(f"Day {self.game.state.current_day}")
            print(f"Player {self.game.get_current_player()}'s turn")
            print(self.game.state)
        elif mode == "raw":
            pp = pprint.PrettyPrinter()
            pp.pprint(self.game.get_observation())
    
    def seed(self, seed=0):
        random.seed(seed)