from Game.State import State
from Game.CO import BaseCO
from Game.Terrain import TerrainLibrary, standard_terrain
from Game.Unit import UnitLibrary, standard_units
from Game.Action import ActionMove, ActionDirectAttack

import pytest

# Test attacking

# Direct can attack valid unit in range
def test_direct_can_attack_valid_in_range(generate_test_game):
    units = {(0, 0): ("INF", "O"), (0, 1): ("INF", "B")}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)    
    attack_action = ActionDirectAttack(ActionMove(unit_position=(0, 0), offset=(0, 0)), (0, 1))
    game.execute_action(attack_action)

    test_unit = game.state.get_unit((0, 0))
    enemy_unit = game.state.get_unit((0, 1))
    assert test_unit and enemy_unit.health < enemy_unit.max_health
    assert enemy_unit and test_unit.health < test_unit.max_health

# Direct can move and attack
def test_direct_can_move_and_attack(generate_test_game):
    units = {(0, 0): ("INF", "O"), (0, 2): ("INF", "B")}
    terrain = [["PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)    
    attack_action = ActionDirectAttack(ActionMove(unit_position=(0, 0), offset=(0, 1)), (0, 1))
    game.execute_action(attack_action)

    test_unit = game.state.get_unit((0, 1))
    enemy_unit = game.state.get_unit((0, 2))
    assert test_unit and enemy_unit.health < enemy_unit.max_health
    assert enemy_unit and test_unit.health < test_unit.max_health

# Direct attack induces counterattack
def test_direct_attack_induces_counterattack(generate_test_game):
    units = {(0, 0): ("TNK", "O"), (0, 1): ("TNK", "B")}
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)    

    attack_action = ActionDirectAttack(ActionMove(unit_position=(0, 0), offset=(0, 0)), (0, 1))
    game.execute_action(attack_action)
    
    test_unit = game.state.get_unit((0, 0))
    assert test_unit.health < test_unit.max_health

# Attacker can self destruct
def test_attacker_can_self_destruct(generate_test_game):
    units = {(0, 0): ("INF", "O"), (0, 2): ("MGT", "B")}
    terrain = [["PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)    

    attack_action = ActionDirectAttack(ActionMove(unit_position=(0, 0), offset=(0, 1)), (0, 1))
    game.execute_action(attack_action)

    assert game.state.get_unit((0, 2), owner='B') is not None
    assert game.state.get_unit((0, 1), owner='O') is None
