from util import load_map
from Game.Unit import UnitLibrary, standard_units
from Game.Terrain import TerrainLibrary, Property, standard_terrain
from Game.State import State
import random
import copy
import numpy as np

class Game:
    def __init__(self, players, init_state=None, allowed_terrain=standard_terrain, allowed_units=standard_units, seed=0, save_history=True):
        self.state = init_state
        self.history = []
        self.seed = seed
        self.players = players
        self.allowed_terrain = allowed_terrain
        self.allowed_units = allowed_units
        self.map_height = self.state.map_height
        self.map_width = self.state.map_width
        self.save_history = save_history

        self.terrain_indices = {terrain_type: i for i, terrain_type in enumerate(self.get_terrain_list())}
        self.property_indices = {terrain_type: i for i, terrain_type in enumerate(self.get_property_list())}
        self.unit_indices = {unit_type: i for i, unit_type in enumerate(allowed_units)}

    @classmethod
    def load_map(cls, players_co, map_path, allowed_terrain=standard_terrain, allowed_units=standard_units, seed=0, save_history=True):
        players = list(players_co.keys())
        
        terrain_library = TerrainLibrary(players, allowed_terrain)
        unit_library = UnitLibrary(allowed_units)

        terrain, units = load_map(map_path, terrain_library, unit_library)
        state = State(players_co, terrain, units)
        game = cls(players=players, init_state=state, seed=seed, save_history=save_history)

        return game
        
    def get_observation(self, player):
        height = self.map_height
        width = self.map_width

        observation = {
            'terrain': np.zeros((len(self.terrain_indices), height, width), dtype=int),
            'properties': np.zeros((len(self.players), len(self.property_indices), height, width), dtype=int),
            'units': np.zeros((len(self.players), len(self.unit_indices), 3, height, width), dtype=int),
            'funds': np.zeros((len(self.players)), dtype=int)
        }

        get_terrain = self.state.get_terrain
        get_property = self.state.get_property
        get_unit = self.state.get_unit

        for r in range(height):
            for c in range(width):
                position = (r, c)
                terrain = get_terrain(position)
                if not isinstance(terrain, Property):
                    observation['terrain'][self.terrain_indices[type(terrain)], r, c] = 1

                for p in self.players:
                    p_id = 0 if p is player else 1
                    property = get_property(position, owner=p)
                    if property is not None:
                        observation['properties'][p_id, self.property_indices[type(property)], r, c] = 1

                    unit = get_unit(position, owner=p)
                    if unit is not None:
                        observation['units'][p_id, self.unit_indices[type(unit)], 0, r, c] = unit.get_display_health()
                        observation['units'][p_id, self.unit_indices[type(unit)], 1, r, c] = unit.fuel
                        observation['units'][p_id, self.unit_indices[type(unit)], 2, r, c] = unit.ammo
                    
                    observation['funds'][p_id] = self.state.funds[p]

        return observation

    def get_players_list(self):
        return self.players
    
    def get_terrain_list(self):
        return [terrain for terrain in self.allowed_terrain if not issubclass(terrain, Property)]

    def get_property_list(self):
        return [terrain for terrain in self.allowed_terrain if issubclass(terrain, Property)]

    def get_unit_list(self):
        return self.allowed_units

    def get_current_player(self):
        return self.state.get_current_player()

    def execute_action(self, action):
        if not action.validated:
            is_valid = action.validate(self.state)
            if not is_valid:
                raise Exception(f"{action}: {action.invalid_message}")

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
