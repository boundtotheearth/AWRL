from Game.State import State
from Game.CO import BaseCO
from Game.Terrain import TerrainLibrary, standard_terrain
from Game.Unit import UnitLibrary, standard_units
from Game.Action import ActionMoveCombineLoad, ActionMove

import pytest
import math

# Can move to traversable terrain inside move range
def test_can_move_to_traversable_in_range(generate_test_game):
    units = {(0, 0): ("INF", 'O')}
    terrain = [["PLN", "PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 3)))
    game.execute_action(move_action)
    
    assert game.state.get_unit((0, 3), owner='O') is not None

# Cannot move outside move range
def test_cannot_move_outside_range(generate_test_game):
    units = {(0, 0): ("INF", "O")}
    
    terrain = [["PLN", "PLN", "PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 4)))
    with pytest.raises(Exception):
        game.execute_action(move_action)
    
# Cannot move out of bounds
def test_cannot_move_out_of_bounds(generate_test_game):
    units = {(0, 0): ("INF", "O")}
    terrain = [["PLN"]]
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))
    with pytest.raises(Exception):
        game.execute_action(move_action)

# Cannot move to occupied space within move range
def test_cannot_move_to_enemy_occupied_space(generate_test_game):
    units = {(0, 0): ("INF", "O"), (0, 1): ("INF", "B")}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))
    with pytest.raises(Exception):
        game.execute_action(move_action)

# Cannot move to untraversable terrain within move range
def test_cannot_move_to_untraversable_terrain(generate_test_game):
    units = {(0, 0): ("INF", 'O')}
    terrain = [["PLN", "SEA"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))
    with pytest.raises(Exception):
        game.execute_action(move_action)

# Cannot move through enemy unit
def test_cannot_move_through_enemy_unit(generate_test_game):
    units = {(0, 0): ("INF", "O"), (0, 1): ("INF", "B")}
    terrain = [["PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)

    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 2)))
    with pytest.raises(Exception):
        game.execute_action(move_action)

# Move consumes fuel
def test_move_fuel_consumption(generate_test_game, terrain_library, unit_library):
    test_unit = unit_library.create("REC", "O")
    road_terrain = terrain_library.create("ROD")
    plain_terrain = terrain_library.create("PLN")
    wood_terrain = terrain_library.create("WOD")
    expected_fuel_consumption = road_terrain.costs[test_unit.move_type] + plain_terrain.costs[test_unit.move_type] + wood_terrain.costs[test_unit.move_type]
    
    units = {(0, 0): test_unit}
    terrain = [[road_terrain, road_terrain, plain_terrain, wood_terrain]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 3)))

    game.execute_action(move_action)

    assert (test_unit.max_fuel - test_unit.fuel) == expected_fuel_consumption

# Move limited by terrain movement costs
def test_move_limited_by_terrain_movement_costs(generate_test_game, terrain_library):
    road_terrain = terrain_library.create("ROD")
    mountain_terrain = terrain_library.create("MTN")
    wood_terrain = terrain_library.create("WOD")
    road_terrain_2 = terrain_library.create("ROD")
    
    units = {(0, 0): ("INF", "O")}
    
    terrain = [[road_terrain, road_terrain_2, mountain_terrain, wood_terrain]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 3)))

    with pytest.raises(Exception) as e:
        game.execute_action(move_action)

# Can combine with same type unit with missing health
def test_can_combine_with_same_type_unit_missing_health(generate_test_game, unit_library):
    initial_target_health = 9
    target_unit = unit_library.create("INF", owner='O', health=initial_target_health)
    
    units = {(0, 0): ("INF", "O"), (0, 1): target_unit}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))

    game.execute_action(move_action)
    
    assert game.state.get_unit((0, 0), owner='O') is None
    assert game.state.get_unit((0, 1), owner='O') == target_unit
    assert target_unit.health > initial_target_health

# Combined health does not exceed max health
def test_combine_health_does_not_exceed_max_health(generate_test_game, unit_library):
    initial_target_health = 89
    target_unit = unit_library.create("INF", owner='O', health=initial_target_health)
    units = {(0, 0): ("INF", "O"), (0, 1): target_unit}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))

    game.execute_action(move_action)
    
    assert target_unit.health == target_unit.max_health

# Excess funds added if combined health exceeds max health
def test_excess_funds_added_if_more_than_max_health(generate_test_game, unit_library):
    test_unit = unit_library.create("INF", "O", health=89)
    target_unit = unit_library.create("INF", "O", health=89)
    
    expected_funds = (((test_unit.get_display_health() + target_unit.get_display_health()) - 10) / 10) * target_unit.cost
    
    units = {(0, 0): test_unit, (0, 1): target_unit}
    
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    initial_funds = game.state.funds['O']
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))

    game.execute_action(move_action)

    assert (game.state.funds['O'] - initial_funds) == expected_funds

# Cannot combine with full health unit
def test_cannot_combine_with_full_health_unit(generate_test_game):
    units = {(0, 0): ("INF", "O"), (0, 1): ("INF", "O")}
    terrain = [["PLN", "PLN"]]
    game = generate_test_game(terrain=terrain, units=units)
    
    blocking_unit = game.state.get_unit((0, 1))
    assert blocking_unit.health == blocking_unit.max_health

    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))
    with pytest.raises(Exception):
        game.execute_action(move_action)

# Cannot combine with different type unit
def test_cannot_combine_with_different_type_unit(generate_test_game):    
    units = {(0, 0): ("INF", "O"), (0, 1): ("TNK", "O")}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))

    with pytest.raises(Exception):
        game.execute_action(move_action)

# Cannot combine with enemy unit
def test_cannot_combine_with_enemy_unit(generate_test_game, unit_library):
    target_unit = unit_library.create("INF", owner='B', health=49)
    units = {(0, 0): ("INF", "O"), (0, 1): target_unit}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))

    with pytest.raises(Exception):
        game.execute_action(move_action)

# Cannot combine with self
def test_cannot_combine_with_self(generate_test_game):
    

    units = {(0, 0): ("INF", "O")}
    terrain = [["PLN"]]
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 0)))

    with pytest.raises(Exception):
        game.execute_action(move_action)

# Can load unit into valid transport unit
def test_can_load_into_valid_transport(generate_test_game, unit_library):
    test_unit = unit_library.create("INF", "O")
    units = {(0, 0): test_unit, (0, 1): ("APC", 'O')}
    terrain = [["PLN", "PLN"]]
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))
    
    game.execute_action(move_action)
    
    assert game.state.get_unit((00, 0), owner='O') is None
    assert test_unit in game.state.get_unit((0, 1)).in_load

# Can load multiple units
def test_can_load_multiple_units(generate_test_game, unit_library):
    test_unit = unit_library.create("INF", "O")
    test_unit_2 = unit_library.create("INF", "O")
    transport_unit = unit_library.create("LND", "O")
    units = {(0, 0): test_unit, (0, 1): test_unit_2, (0, 2): transport_unit}
    terrain = [["PLN", "PLN", "SHL"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 2)))
    
    game.execute_action(move_action)
    
    move_action_2 = ActionMoveCombineLoad(ActionMove(unit_position=(0, 1), offset=(0, 1)))
    
    game.execute_action(move_action_2)
    
    assert game.state.get_unit((0, 0), owner='O') is None
    assert game.state.get_unit((0, 1), owner='O') is None
    assert test_unit in transport_unit.in_load
    assert test_unit_2 in transport_unit.in_load

# Cannot load unit into non transport unit
def test_cannot_load_into_non_transport(generate_test_game):
    units = {(0, 0): ("INF", 'O'), (0, 1): ("INF", 'O')}
    terrain = [["PLN", "PLN"]]
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))
    
    with pytest.raises(Exception):
        game.execute_action(move_action)
    
# Cannot load unit into enemy transport unit
def test_cannot_load_into_enemy_transport(generate_test_game):
    units = {(0, 0): ("INF", 'O'), (0, 1): ("APC", 'B')}
    terrain = [["PLN", "PLN"]]
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))
    
    with pytest.raises(Exception):
        game.execute_action(move_action)
    
def test_cannot_load_into_full_transport(generate_test_game, unit_library):
    loaded_unit = unit_library.create("INF", "O")
    loaded_unit_2 = unit_library.create("INF", "O")
    transport_unit = unit_library.create("LND", "O")
    transport_unit.load(loaded_unit)
    transport_unit.load(loaded_unit_2)

    units = {(0, 0): ("INF", 'O'), (0, 1): transport_unit}
    terrain = [["PLN", "SHL"]]
    game = generate_test_game(terrain=terrain, units=units)
    
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))
    
    with pytest.raises(Exception):
        game.execute_action(move_action)
