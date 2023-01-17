from util import load_map
from Game.Unit import UnitLibrary, standard_units
from Game.Terrain import TerrainLibrary, Property, standard_terrain
from Game.State import State
import random
import copy
import numpy as np

class Game:
    def __init__(self, players, init_state=None, allowed_terrain=standard_terrain, allowed_units=standard_units, seed=0, save_history=True, strict=True):
        self.state = init_state
        self.history = []
        self.seed = seed
        self.players = players
        self.allowed_terrain = allowed_terrain
        self.allowed_units = allowed_units
        self.map_height = self.state.map_height
        self.map_width = self.state.map_width
        self.save_history = save_history
        self.strict = strict

    @classmethod
    def load_map(cls, players_co, map_path, allowed_terrain=standard_terrain, allowed_units=standard_units, seed=0, save_history=True, strict=True):
        players = list(players_co.keys())
        
        terrain_library = TerrainLibrary(players, allowed_terrain)
        unit_library = UnitLibrary(allowed_units)

        terrain, units = load_map(map_path, terrain_library, unit_library)
        state = State(players_co, terrain, units)
        game = cls(players=players, init_state=state, seed=seed, save_history=save_history, strict=strict)

        return game

    def get_players_list(self):
        return self.players

    def get_current_player(self):
        return self.state.get_current_player()

    def execute_action(self, action):
        if not action.validated:
            is_valid = action.validate(self.state)
            if not is_valid:
                if self.strict:
                    raise Exception(f"{action}: {action.invalid_message}")
                else:
                    print(f"INVALID ACTION {action}: {action.invalid_message}")
                    return self.state.check_winner()

        action.execute()

        if self.save_history:
            self.record_action(action)

        return self.state.check_winner()

    def record_action(self, action):
        self.history.append(
            (
                copy.deepcopy(action),
                copy.deepcopy(self.state)
            )
        )

    def __str__(self):
        output = ""
        output += "Day: {}\n".format(self.state.current_day)
        output += "Funds: {}\n".format(self.state.funds)
        output += "Current Player: {}\n".format(self.state.players[self.state.current_player])
        output += str(self.state) + "\n"
        return output
