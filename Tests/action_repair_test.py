from Game.State import State
from Game.CO import BaseCO
from Game.Terrain import TerrainLibrary, standard_terrain
from Game.Unit import UnitLibrary, standard_units
from Game.Action import ActionRepair, ActionMove

import pytest

# Test repair

# Can repair land unit in range
def test_can_repair_land_unit(generate_test_game, unit_library):
    target_unit = unit_library.create("INF", "O", health=89)
    units = {(0, 0): ("BLB", 'O'), (0, 1): target_unit}
    terrain = [["SEA", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    initial_funds = game.state.funds['O']
    repair_action = ActionRepair(ActionMove(unit_position=(0, 0), offset=(0, 0)), repair_offset=(0, 1))

    game.execute_action(repair_action)

    assert target_unit.health == 99
    assert game.state.funds['O'] == initial_funds - (target_unit.cost // 10)

# Can repair air unit in range
def test_can_repair_air_unit(generate_test_game, unit_library):
    target_unit = unit_library.create("FGT", "O", health=89)

    units = {(0, 0): ("BLB", 'O'), (0, 1): target_unit}
    
    terrain = [["SEA", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    initial_funds = game.state.funds['O']
    repair_action = ActionRepair(ActionMove(unit_position=(0, 0), offset=(0, 0)), repair_offset=(0, 1))

    game.execute_action(repair_action)
    
    assert target_unit.health == 99
    assert game.state.funds['O'] == initial_funds - target_unit.cost // 10

# Can repair sea unit in range
def test_can_repair_sea_unit(generate_test_game, unit_library):
    target_unit = unit_library.create("CRU", "O", health=89)

    units = {(0, 0): ("BLB", 'O'), (0, 1): target_unit}
    terrain = [["SEA", "SEA"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    initial_funds = game.state.funds['O']
    repair_action = ActionRepair(ActionMove(unit_position=(0, 0), offset=(0, 0)), repair_offset=(0, 1))

    game.execute_action(repair_action)
    
    assert target_unit.health == 99
    assert game.state.funds['O'] == initial_funds - target_unit.cost // 10

# Can move and repair
def test_can_move_and_repair(generate_test_game, unit_library):
    target_unit = unit_library.create("INF", "O", health=89)
    units = {(0, 0): ("BLB", 'O'), (0, 3): target_unit}
    terrain = [["SEA", "SEA", "SEA", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    initial_funds = game.state.funds['O']
    repair_action = ActionRepair(ActionMove(unit_position=(0, 0), offset=(0, 2)), repair_offset=(0, 1))

    game.execute_action(repair_action)
    
    assert target_unit.health == 99
    assert game.state.funds['O'] == initial_funds - target_unit.cost // 10

# Cannot repair if not enough funds
def test_cannot_repair_if_not_enough_funds(generate_test_game, unit_library):
    target_unit = unit_library.create("INF", "O", health=89)
    units = {(0, 0): ("BLB", 'O'), (0, 1): target_unit}
    terrain = [["SEA", "PLN"]]
    funds = {'O': 0, 'B': 0}
    
    game = generate_test_game(terrain=terrain, units=units, funds=funds)
    
    repair_action = ActionRepair(ActionMove(unit_position=(0, 0), offset=(0, 0)), repair_offset=(0, 1))

    with pytest.raises(Exception):
        game.execute_action(repair_action)
    
# Cannot repair if no target
def test_cannot_repair_if_no_target(generate_test_game):
    units = {(0, 0): ("BLB", "O")}
    terrain = [["SEA", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    repair_action = ActionRepair(ActionMove(unit_position=(0, 0), offset=(0, 0)), repair_offset=(0, 1))

    with pytest.raises(Exception):
        game.execute_action(repair_action)

# Cannot repair if out of range
def test_cannot_repair_if_out_of_range(generate_test_game):
    units = {(0, 0): ("BLB", "O"), (0, 2): ("INF", "O")}
    terrain = [["SEA", "SEA", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    repair_action = ActionRepair(ActionMove(unit_position=(0, 0), offset=(0, 0)), repair_offset=(0, 1))

    with pytest.raises(Exception):
        game.execute_action(repair_action)

# Cannot repair enemy unit
def test_cannot_repair_enemy_unit(generate_test_game):
    units = {(0, 0): ("BLB", "O"), (0, 1): ("INF", "B")}
    terrain = [["SEA", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    repair_action = ActionRepair(ActionMove(unit_position=(0, 0), offset=(0, 0)), repair_offset=(0, 1))

    with pytest.raises(Exception):
        game.execute_action(repair_action)

# Repair also resupplies
def test_repair_also_resupplies(generate_test_game, unit_library):
    target_unit = unit_library.create("TNK", "O", fuel=0, ammo=0)
    
    units = {(0, 0): ("BLB", "O"), (0, 1): target_unit}
    
    terrain = [["SEA", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    repair_action = ActionRepair(ActionMove(unit_position=(0, 0), offset=(0, 0)), repair_offset=(0, 1))

    game.execute_action(repair_action)
    
    assert target_unit.fuel == target_unit.max_fuel
    assert target_unit.ammo == target_unit.max_ammo

# Units that cannot repair
def test_units_that_cannot_repair(generate_test_game):
    
    units = {(0, 0): ("INF", "O"), (0, 1): ("INF", "O")}
    
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    repair_action = ActionRepair(ActionMove(unit_position=(0, 0), offset=(0, 0)), repair_offset=(0, 1))

    with pytest.raises(Exception):
        game.execute_action(repair_action)
