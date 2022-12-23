from Game.State import State
from Game.CO import BaseCO
from Game.Terrain import Terrain, TerrainLibrary, standard_terrain
from Game.Unit import Unit, UnitLibrary, standard_units
from Game.Game import Game

import pytest
import copy

@pytest.fixture
def base_cos():
    return {
        "O": BaseCO(),
        "B": BaseCO()
    }

@pytest.fixture
def max_funds():
    return {
        "O": 100000,
        "B": 100000
    }

@pytest.fixture
def terrain_library(base_cos):
    return TerrainLibrary(list(base_cos.keys()), standard_terrain)

@pytest.fixture(scope='module',)
def unit_library():
    return UnitLibrary(standard_units)

@pytest.fixture
def generate_state(base_cos, max_funds):
    def generator(co=base_cos, terrain=[[]], units={}, funds=max_funds):
        terrain_library = TerrainLibrary(list(co.keys()), standard_terrain)
        unit_library = UnitLibrary(standard_units)
        terrain = [[terrain_library.create(terrain) if not isinstance(terrain, Terrain) else terrain for terrain in row] for row in terrain]
        units = {position: unit if isinstance(unit, Unit) else unit_library.create(unit[0], unit[1]) for position, unit in units.items()}
        return State(co=co, terrain=terrain, units=units, funds=funds)

    return generator

@pytest.fixture
def generate_test_game(base_cos, generate_state, max_funds):
    def generator(co=base_cos, terrain=[[]], units={}, funds=max_funds):
        init_state = generate_state(co, terrain, units, funds)
        players = list(co.keys())
        return Game(players=players, init_state=init_state, seed=0, save_history=False)

    return generator
