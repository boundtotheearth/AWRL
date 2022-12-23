from Game.Action import ActionAttack, ActionMove
import pytest

# Test attacking
# Destroyed unit is removed
def test_destroyed_unit_is_removed(generate_test_game):
    units = {
        (0, 0): ("MGT", "O"), 
        (0, 1): ("INF", "B")
    }
    
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)

    enemy_unit = game.state.get_unit((0, 1))
    test_unit = game.state.get_unit((0, 0))
    
    attack_action = ActionAttack(ActionMove(unit_position=(0, 0), offset=(0, 0)), attack_offset=(0, 1))
    game.execute_action(attack_action)

    assert enemy_unit.get_display_health() <= 0
    assert game.state.get_unit((0, 1), owner='B') is None
    assert test_unit.health == test_unit.max_health

# Cannot attack own unit
def test_cannot_attack_own_unit(generate_test_game):    
    units = {
        (0, 0): ("INF", "O"), 
        (0, 1): ("INF", "O")
    }
    
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    attack_action = ActionAttack(ActionMove(unit_position=(0, 0), offset=(0, 0)), attack_offset=(0, 1))
    with pytest.raises(Exception):
        game.execute_action(attack_action)
    
# Cannot attack out of range
def test_cannot_attack_out_of_range(generate_test_game):    
    units = {
        (0, 0): ("INF", "O"), 
        (0, 2): ("INF", "B")
    }
    terrain = [["PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    attack_action = ActionAttack(ActionMove(unit_position=(0, 0), offset=(0, 0)), attack_offset=(0, 2))

    with pytest.raises(Exception):
        game.execute_action(attack_action)

# Cannot attack out of bounds
def test_cannot_attack_out_of_bounds(generate_test_game):
    units = {(0, 0): ("INF", "O")}
    terrain = [["PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    attack_action = ActionAttack(ActionMove(unit_position=(0, 0), offset=(0, 0)), attack_offset=(0, 1))

    with pytest.raises(Exception):
        game.execute_action(attack_action)

# Cannot attack target if not in damage table
def test_cannot_attack_if_not_in_damage_table(generate_test_game):
    units = {
        (0, 0): ("INF", "O"), 
        (0, 1): ("FGT", "O")
    }
    
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)

    attack_action = ActionAttack(ActionMove(unit_position=(0, 0), offset=(0, 0)), attack_offset=(0, 1))
    
    with pytest.raises(Exception):
        game.execute_action(attack_action)

# Cannot attack after combine
def test_cannot_attack_after_combine(generate_test_game):
    units = {
        (0, 0): ("INF", "O"), 
        (0, 1): ("INF", "O"), 
        (0, 2): ("INF", "B")
    }
    
    terrain = [["PLN", "PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)

    attack_action = ActionAttack(ActionMove(unit_position=(0, 0), offset=(0, 1)), attack_offset=(0, 1))
    
    with pytest.raises(Exception):
        game.execute_action(attack_action)

# Attack consumes ammo
def test_attack_consumes_ammo(generate_test_game, unit_library):
    test_unit = unit_library.create("TNK", 'O')
    enemy_unit = unit_library.create("INF", 'B')
    
    units = {
        (0, 0): test_unit, 
        (0, 1): enemy_unit
    }

    expected_ammo_consumption = test_unit.attack_table[type(enemy_unit)][1]
    
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)

    attack_action = ActionAttack(ActionMove(unit_position=(0, 0), offset=(0, 0)), attack_offset=(0, 1))
    game.execute_action(attack_action)
    assert (test_unit.max_ammo - test_unit.ammo) == expected_ammo_consumption

# Cannot attack using primary if no ammo
def test_cannot_attack_with_primary_if_no_ammo(generate_test_game, unit_library):
    test_unit = unit_library.create("TNK", 'O')
    test_unit.ammo = 0

    units = {
        (0, 0): test_unit, 
        (0, 1): ("TNK", "B")
    }
    
    terrain = [["PLN", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)

    attack_action = ActionAttack(ActionMove(unit_position=(0, 0), offset=(0, 0)), attack_offset=(0, 1))
    with pytest.raises(Exception):
        game.execute_action(attack_action)

#TODO: Can use secondary on valid targets if primary is out of ammo

#TODO: Using secondary does not consume ammo