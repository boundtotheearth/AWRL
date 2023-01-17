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

def calculate_damage(attacking_co, attacking_unit, defending_co, defending_unit, terrain, CT):
    base_damage = attacking_unit.attack_table.get(type(defending_unit), ())[0]
    if base_damage is None:
        raise Exception("{attacker} cannot attack {defender}".format(attacker=attacking_unit, defender=defending_unit))
    co_attack = attacking_co.get_attack_modifier(type(attacking_unit))
    luck = attacking_co.get_luck_roll()
    attacker_visual_health = attacking_unit.get_display_health()
    co_defense = defending_co.get_defence_modifier(type(defending_unit))
    terrain_stars = terrain.defence
    defender_visual_health = defending_unit.get_display_health()
    ct_attack = CT * 10

    final_damage = (((base_damage * (co_attack + ct_attack)) / 100) + luck) * (attacker_visual_health / 10) * ((200 - (co_defense + (terrain_stars * defender_visual_health))) / 100)

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

awbw_terrain_id_code_map = {
    1: "PLN",
    2: "MTN",
    3: "WOD",
    4: "RVR",
    5: "RVR",
    6: "RVR",
    7: "RVR",
    8: "RVR",
    9: "RVR",
    10: "RVR",
    11: "RVR",
    12: "RVR",
    13: "RVR",
    14: "RVR",
    15: "ROD",
    16: "ROD",
    17: "ROD",
    18: "ROD",
    19: "ROD",
    20: "ROD",
    21: "ROD",
    22: "ROD",
    23: "ROD",
    24: "ROD",
    25: "ROD",
    26: "ROD",
    27: "ROD",
    28: "SEA",
    29: "SHL",
    30: "SHL",
    31: "SHL",
    32: "SHL",
    33: "REF",
    34: "NCT",
    35: "NBS",
    36: "NAP",
    37: "NPT",
    38: "OCT",
    39: "OBS",
    40: "OAP",
    41: "OPT",
    42: "OHQ",
    43: "BCT",
    44: "BBS",
    45: "BAP",
    46: "BPT",
    47: "BHQ",
    112: "SIL"
}
def awbw_terrain_id_to_code(awbw_terrain_id):
    return awbw_terrain_id_code_map[int(awbw_terrain_id)]

terrain_code_awbw_id_map = {v: k for k, v in awbw_terrain_id_code_map.items()}
def terrain_code_to_awbw_id(terrain_code):
    return terrain_code_awbw_id_map[terrain_code]

awbw_unit_id_code_map = {
    1: "INF",
    2: "MEC",
    3: "MTK",
    4: "TNK",
    5: "REC",
    6: "APC",
    7: "ATY",
    8: "ROC",
    9: "AAR",
    10: "MIS",
    11: "FGT",
    12: "BMB",
    13: "BCP",
    14: "TCP",
    15: "BSP",
    16: "CRU",
    17: "LND",
    18: "SUB",
    46: "NTK",
    960900: "PRN",
    968731: "BBB",
    1141438: "MGT",
    28: "BLB",
    30: "STH",
    29: "CAR"
}
def awbw_unit_id_to_code(awbw_unit_id):
    return awbw_unit_id_code_map[int(awbw_unit_id)]

unit_code_awbw_id_map = {v: k for k, v in awbw_unit_id_code_map.items()}
def unit_code_to_awbw_id(unit_code):
    return unit_code_awbw_id_map[unit_code]

awbw_country_code_player_map = {
    "os": "O",
    "bm": "B"
}
def awbw_country_code_to_player(country_code):
    return awbw_country_code_player_map[country_code]

player_awbw_country_code_map = awbw_country_code_player_map
def player_to_awbw_country_code(player):
    return player_awbw_country_code_map[player]