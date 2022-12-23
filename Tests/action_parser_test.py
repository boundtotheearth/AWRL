from ActionParser import ActionParser
from Game.CO import BaseCO
from Game.Terrain import TerrainLibrary, standard_terrain
from Game.Unit import UnitLibrary, standard_units
from Game.State import State

def test_parse_end(generate_test_game):
    test_command = "end"

    terrain = [["PLN"]]
    units = {(0, 0): ("FGT", "O")}

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    game.execute_action(action)

    test_unit = game.state.get_unit((0, 0), owner="O")
    assert test_unit.fuel == test_unit.max_fuel - test_unit.daily_fuel

def test_parse_move(generate_test_game):
    test_command = "move 0,0 0,3"

    terrain = [["PLN", "PLN", "PLN", "PLN"]]
    units = {(0, 0): ("INF", "O")}

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    assert game.state.get_unit((0, 3), 'O') is not None

def test_parse_attack(generate_test_game):
    test_command = "attack 0,0 0,0 0,1"

    terrain = [["PLN", "PLN"]]
    units = {(0, 0): ("INF", "O"), (0, 1): ("INF", "B")}

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    enemy_unit = game.state.get_unit((0, 1), owner="B")
    assert enemy_unit.health < enemy_unit.max_health

def test_parse_move_and_attack(generate_test_game):
    test_command = "attack 0,0 0,2 0,1"

    terrain = [["PLN", "PLN", "PLN", "PLN"]]
    units = {(0, 0): ("INF", "O"), (0, 3): ("INF", "B")}

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    enemy_unit = game.state.get_unit((0, 3), owner="B")
    assert enemy_unit.health < enemy_unit.max_health

def test_parse_indirect_attaack(generate_test_game):
    test_command = "attack 0,0 0,0 0,3"

    units = {(0, 0): ("ATY", "O"), (0, 3): ("INF", "B")}
    terrain = [["PLN", "PLN", "PLN", "PLN"]]

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    enemy_unit = game.state.get_unit((0, 3), owner="B")
    assert enemy_unit.health < enemy_unit.max_health

def test_parse_capture(generate_test_game):
    test_command = "capture 0,0 0,0"

    terrain = [["NCT"]]
    units = {(0, 0): ("INF", "O")}

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    assert game.state.get_property((0, 0)).capture_amount < 20

def test_parse_move_and_capture(generate_test_game):
    test_command = "capture 0,0 0,3"

    terrain = [["PLN", "PLN", "PLN", "NCT"]]
    
    units = {(0, 0): ("INF", "O")}

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    test_property = game.state.get_property((0, 3))
    assert test_property.capture_amount < 20

def test_parse_build(generate_test_game):
    test_command = "build 0,0 INF"

    terrain = [["OBS"]]
    
    game = generate_test_game(terrain=terrain)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    built_unit = game.state.get_unit((0, 0), "O")
    assert built_unit is not None
    assert built_unit.code == "INF"

def test_parse_repair(generate_test_game):
    test_command = "repair 0,0 0,0 0,1"

    terrain = [["PLN", "PLN"]]
    units = {(0, 0): ("BLB", "O"), (0, 1): ("INF", "O")}

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    repair_unit = game.state.get_unit((0, 1), owner="O")
    assert repair_unit.health == repair_unit.max_health

def test_parse_move_and_repair(generate_test_game, unit_library):
    test_command = "repair 0,0 0,2 0,1"

    target_unit = unit_library.create("INF", "O", health=89)
    terrain = [["SEA", "SEA", "SEA", "PLN"]]
    units = {(0, 0): ("BLB", "O"), (0, 3): target_unit}

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    assert target_unit.health == 99

def test_parse_unload(generate_test_game, unit_library):
    test_command = "unload 0,0 0,0 0,1 0"

    terrain = [["PLN", "PLN"]]
    loaded_unit = unit_library.create("INF", "O")
    test_unit = unit_library.create("APC", "O", to_load=[loaded_unit])
    
    units = {(0, 0): test_unit}

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    assert game.state.get_unit((0, 1), "O") == loaded_unit

def test_parse_move_and_unload(generate_test_game, unit_library):
    test_command = "unload 0,0 0,2 0,1 0"

    terrain = [["PLN", "PLN", "PLN", "PLN"]]
    loaded_unit = unit_library.create("INF", "O")
    test_unit = unit_library.create("APC", "O", to_load=[loaded_unit])
    
    units = {(0, 0): test_unit}

    game = generate_test_game(terrain=terrain, units=units)

    action = ActionParser().parse(test_command)
    game.execute_action(action)
    
    assert game.state.get_unit((0, 3), "O") == loaded_unit
