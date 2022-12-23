from Game.State import State
from Game.CO import BaseCO
from Game.Terrain import TerrainLibrary, standard_terrain
from Game.Unit import UnitLibrary, standard_units
from Game.Action import ActionDirectAttack, ActionIndirectAttack, ActionMove

import pytest

# Test attacking

# Indirect can attack valid unit in range
def test_indirect_can_attack_valid_in_range(generate_test_game):
    units = {(0, 0): ("ATY", "O"), (0, 3): ("INF", "B")}
    terrain = [["PLN", "PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    attack_action = ActionIndirectAttack(unit_position=(0, 0), attack_offset=(0, 3))

    game.execute_action(attack_action)

    test_unit = game.state.get_unit((0, 0))
    enemy_unit = game.state.get_unit((0, 3))
    assert enemy_unit.health < enemy_unit.max_health
    assert test_unit.health == test_unit.max_health

# Indirect cannot counterattack direct
def test_indirect_cannot_counterattack_direct(generate_test_game):
    units = {(0, 0): ("TNK", "O"), (0, 1): ("ATY", "B")}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)

    attack_action = ActionDirectAttack(ActionMove(unit_position=(0, 0), offset=(0, 0)), (0, 1))
    game.execute_action(attack_action)
    
    test_unit = game.state.get_unit((0, 0))
    assert test_unit.health == test_unit.max_health
