from Game.State import State
from Game.CO import BaseCO
from Game.Terrain import TerrainLibrary, standard_terrain
from Game.Unit import UnitLibrary, standard_units
from Game.Action import ActionMove, ActionUnload, ActionEnd

import pytest

# Test unload

# Can unload unit in range
def test_can_unload_unit(generate_test_game, unit_library):
    loaded_unit = unit_library.create("INF", 'O')
    test_unit = unit_library.create("APC", 'O', to_load=[loaded_unit])
    
    units = {(0, 0): test_unit}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 0), offset=(0, 0)), unload_offset=(0, 1), idx=0)

    game.execute_action(unload_action)
    
    assert game.state.get_unit((0, 1), 'O') == loaded_unit
    assert loaded_unit not in test_unit.in_load

# Can unload multiple units
def test_can_multiple_units(generate_test_game, unit_library):
    loaded_unit = unit_library.create("INF", 'O')
    loaded_unit_2 = unit_library.create("INF", 'O')
    test_unit = unit_library.create("LND", 'O', to_load=[loaded_unit, loaded_unit_2])
    
    units = {(0, 1): test_unit}
    
    terrain = [["PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 1), offset=(0, 0)), unload_offset=(0, 1), idx=0)
    game.execute_action(unload_action)
    
    game.execute_action(ActionEnd())
    game.execute_action(ActionEnd())

    unload_action = ActionUnload(ActionMove(unit_position=(0, 1), offset=(0, 0)), unload_offset=(0, -1), idx=0)
    game.execute_action(unload_action)
    
    assert game.state.get_unit((0, 2), 'O') == loaded_unit
    assert loaded_unit not in test_unit.in_load
    assert game.state.get_unit((0, 0), 'O') == loaded_unit_2
    assert loaded_unit_2 not in test_unit.in_load

# Can move and unload
def test_can_move_and_unload(generate_test_game, unit_library):
    
    loaded_unit = unit_library.create("INF", 'O')
    test_unit = unit_library.create("APC", 'O', to_load=[loaded_unit])
    units = {(0, 0): test_unit}
    
    terrain = [["PLN", "PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 0), offset=(0, 2)), unload_offset=(0, 1), idx=0)

    game.execute_action(unload_action)
    
    assert game.state.get_unit((0, 3), 'O') == loaded_unit
    assert loaded_unit not in test_unit.in_load

# Cannot unload if nothing loaded
def test_cannot_unload_if_nothing_loaded(generate_test_game):    
    units = {(0, 0): ("APC", 'O')}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 0), offset=(0, 0)), unload_offset=(0, 1), idx=0)

    with pytest.raises(Exception):
        game.execute_action(unload_action)
    
# Cannot unload if not in range
def test_cannot_unload_if_not_in_range(generate_test_game, unit_library):
    loaded_unit = unit_library.create("INF", 'O')
    test_unit = unit_library.create("APC", 'O', to_load=[loaded_unit])
    
    units = {(0, 0): test_unit}
    terrain = [["PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 0), offset=(0, 0)), unload_offset=(0, 2), idx=0)

    with pytest.raises(Exception):
        game.execute_action(unload_action)

# Cannot unload from empty slot
def test_cannot_unload_from_empty_slot(generate_test_game, unit_library):
    loaded_unit = unit_library.create("INF", 'O')
    test_unit = unit_library.create("APC", 'O', to_load=[loaded_unit])
    
    units = {(0, 0): test_unit}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 0), offset=(0, 0)), unload_offset=(0, 1), idx=1)

    with pytest.raises(Exception):
        game.execute_action(unload_action)

# Cannot unload onto space occupied by own unit
def test_cannot_unload_into_space_occupied_by_own_unit(generate_test_game, unit_library):
    loaded_unit = unit_library.create("INF", 'O')
    test_unit = unit_library.create("APC", 'O', to_load=[loaded_unit])
    
    units = {(0, 0): test_unit, (0, 1): ("INF", 'O')}
    
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 0), offset=(0, 0)), unload_offset=(0, 1), idx=0)

    with pytest.raises(Exception):
        game.execute_action(unload_action)

# Cannot unload into space occupied by enemy unit
def test_cannot_unload_into_space_occupied_by_enemy_unit(generate_test_game, unit_library):
    loaded_unit = unit_library.create("INF", 'O')
    test_unit = unit_library.create("APC", 'O', to_load=[loaded_unit])
    
    units = {(0, 0): test_unit, (0, 1): ("INF", "B")}
    
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 0), offset=(0, 0)), unload_offset=(0, 1), idx=0)

    with pytest.raises(Exception):
        game.execute_action(unload_action)

# Cannot unload onto invalid terrain
def test_cannot_unload_if_nothing_loaded(generate_test_game, unit_library):
    loaded_unit = unit_library.create("INF", 'O')
    test_unit = unit_library.create("APC", 'O', to_load=[loaded_unit])
    
    units = {(0, 0): test_unit}
    terrain = [["PLN", "SEA"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 0), offset=(0, 0)), unload_offset=(0, 1), idx=0)

    with pytest.raises(Exception):
        game.execute_action(unload_action)

# Cannot unload onto out of bounds position
def test_cannot_unload_to_out_of_bounds_position(generate_test_game, unit_library):
    loaded_unit = unit_library.create("INF", 'O')
    test_unit = unit_library.create("APC", 'O', to_load=[loaded_unit])
    
    units = {(0, 0): test_unit}
    terrain = [["PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 0), offset=(0, 0)), unload_offset=(0, 1), idx=0)

    with pytest.raises(Exception):
        game.execute_action(unload_action)

# Cannot unload while on invalid terrain
def test_cannot_unload_while_on_invalid_terrain(generate_test_game, unit_library):
    loaded_unit = unit_library.create("INF", 'O')
    test_unit = unit_library.create("LND", 'O', to_load=[loaded_unit])
    
    units = {(0, 0): test_unit}
    terrain = [["SEA", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    unload_action = ActionUnload(ActionMove(unit_position=(0, 0), offset=(0, 0)), unload_offset=(0, 1), idx=0)

    with pytest.raises(Exception):
        game.execute_action(unload_action)

