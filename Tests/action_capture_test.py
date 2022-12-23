from Game.Action import ActionMove, ActionDirectAttack, ActionCapture, ActionEnd
import pytest

# Test Capturing

# Can capture neutral properties
def test_can_capture_neutral_properties(generate_test_game):
    units = {
        (0, 0): ("INF", "O")
    }

    terrain = [["NCT"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    capture_action = ActionCapture(ActionMove(unit_position=(0, 0), offset=(0, 0)))
    game.execute_action(capture_action)

    capture_target = game.state.get_terrain((0, 0))
    assert capture_target.capture_amount < 20
    assert capture_target.owner == 'N'

    game.execute_action(ActionEnd())
    game.execute_action(ActionEnd())
    
    game.execute_action(capture_action)

    assert capture_target.capture_amount == 20
    assert capture_target.owner == 'O'

# Can capture enemy properties
def test_can_capture_enemy_properties(generate_test_game):
    units = {(0, 0): ("INF", "O")}
    terrain = [["BCT"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    capture_action = ActionCapture(ActionMove(unit_position=(0, 0), offset=(0, 0)))

    game.execute_action(capture_action)

    capture_target = game.state.get_terrain((0, 0))
    assert capture_target.capture_amount < 20
    assert capture_target.owner == 'B'

    game.execute_action(ActionEnd())
    game.execute_action(ActionEnd())
    
    game.execute_action(capture_action)

    assert capture_target.capture_amount == 20
    assert capture_target.owner == 'O'

# Capture amount calculated correctly
def test_capture_amount_correct(generate_test_game, unit_library):
    test_unit = unit_library.create("INF", "O", health=41)
    units = {(0, 0): test_unit}
    terrain = [["NCT"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    capture_action = ActionCapture(ActionMove(unit_position=(0, 0), offset=(0, 0)))

    game.execute_action(capture_action)

    capture_target = game.state.get_terrain((0, 0))
    assert capture_target.capture_amount == 15
    assert capture_target.owner == 'N'

    game.execute_action(ActionEnd())
    game.execute_action(ActionEnd())
    
    game.execute_action(capture_action)

    assert capture_target.capture_amount == 10
    assert capture_target.owner == 'N'

# Capture resets after unit moves away
def test_capture_amount_reset_after_move(generate_test_game):
    units = {(0, 0): ("INF", "O")}
    terrain = [["NCT", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    capture_action = ActionCapture(ActionMove(unit_position=(0, 0), offset=(0, 0)))

    game.execute_action(capture_action)

    capture_target = game.state.get_terrain((0, 0))
    assert capture_target.capture_amount < 20
    assert capture_target.owner == 'N'

    game.execute_action(ActionEnd())
    game.execute_action(ActionEnd())

    game.execute_action(ActionMove((0, 0), (0, 1)))
    
    assert capture_target.capture_amount == 20
    assert capture_target.owner == 'N'

# Capture resets after unit destroyed
def test_capture_amount_reset_after_destroyed(generate_test_game):
    units = {
        (0, 0): ("INF", "O"), 
        (0, 1): ("MGT", "B")
    }
    terrain = [["NCT", "PLN"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    capture_action = ActionCapture(ActionMove(unit_position=(0, 0), offset=(0, 0)))

    game.execute_action(capture_action)

    capture_target = game.state.get_terrain((0, 0))
    assert capture_target.capture_amount < 20
    assert capture_target.owner == 'N'

    game.execute_action(ActionEnd())
    game.execute_action(ActionDirectAttack(ActionMove(unit_position=(0, 1), offset=(0, 0)), (0, -1)))

    assert game.state.get_unit((0, 0), owner='O') is None
    assert capture_target.capture_amount == 20
    assert capture_target.owner == 'N'

# Non infantry/mech cannot capture
def test_non_inf_cannot_capture(generate_test_game):
    units = {(0, 0): ("TNK", "O")}
    terrain = [["NCT"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    capture_action = ActionCapture(ActionMove(unit_position=(0, 0), offset=(0, 0)))

    with pytest.raises(Exception):
        game.execute_action(capture_action)

# Cannot capture own property
def test_cannot_capture_own_property(generate_test_game):
    units = {(0, 0): ("INF", "O")}
    terrain = [["OCT"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    capture_action = ActionCapture(ActionMove(unit_position=(0, 0), offset=(0, 0)))

    with pytest.raises(Exception):
        game.execute_action(capture_action)

# Can move and capture
def test_can_move_and_capture(generate_test_game):
    units = {(0, 0): ("INF", "O")}
    terrain = [["PLN", "NCT"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    capture_action = ActionCapture(ActionMove(unit_position=(0, 0), offset=(0, 1)))

    game.execute_action(capture_action)

    capture_target = game.state.get_terrain((0, 1))
    assert game.state.get_unit((0, 1), 'O') is not None
    assert capture_target.capture_amount < 20
