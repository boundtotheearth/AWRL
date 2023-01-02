import os
import sys
import json
import math
import numpy as np
from collections import OrderedDict
from Game.Terrain import standard_terrain, Property
from Game.Unit import standard_units

def parse_direction(direction_input):
    direction_map = {
        0: (-1, 0),
        1: (1, 0),
        2: (0, 1),
        3: (0, -1)
    }
    return direction_map.get(direction_input)

def parse_direction_reverse(direction_input):
    direction_map = {
        (-1, 0): 0,
        (1, 0): 1,
        (0, 1): 2,
        (0, -1): 3 
    }
    return direction_map.get(direction_input)

def calculate_damage(attacking_co, attacking_unit, defending_co, defending_unit, terrain):
    base_damage = attacking_unit.attack_table.get(type(defending_unit), ())[0]
    if base_damage is None:
        raise Exception("{attacker} cannot attack {defender}".format(attacker=attacking_unit, defender=defending_unit))
    co_attack = attacking_co.get_attack_modifier(type(attacking_unit))
    luck = attacking_co.get_luck_roll()
    attacker_visual_health = attacking_unit.get_display_health()
    co_defense = defending_co.get_defence_modifier(type(defending_unit))
    terrain_stars = terrain.defence
    defender_visual_health = defending_unit.get_display_health()

    final_damage = (((base_damage * co_attack) / 100) + luck) * (attacker_visual_health / 10) * ((200 - (co_defense + (terrain_stars * defender_visual_health))) / 100)

    final_damage = math.ceil(final_damage / 0.05) * 0.05
    final_damage = math.floor(final_damage)
    return final_damage

def load_map(map_path, terrain_library, unit_library):
    with open(map_path, 'r+') as map_file:
        map_data = json.loads(map_file.read())
        
        terrain = [[terrain_library.create(tile) for tile in row] for row in map_data["terrain"]]
        
        units = { 
            (unit_data["row"], unit_data["col"]) : unit_library.create(unit_data["code"], owner)
            for owner, unit_list in map_data['units'].items()
            for unit_data in unit_list
        }
        
    return terrain, units

def linear_schedule(initial_value: float):
    def func(progress_remaining: float) -> float:
        return progress_remaining * initial_value
    return func
