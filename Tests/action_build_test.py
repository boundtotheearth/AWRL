from Game.Action import ActionBuild, ActionMoveCombineLoad, ActionMove
import pytest

# Test Building

# Can build land unit on base
def test_can_build_land_on_base(generate_test_game):    
    terrain = [["OBS"]]
    game = generate_test_game(terrain=terrain)
    
    initial_funds = game.state.funds['O']
    build_action = ActionBuild((0, 0), "INF")
    game.execute_action(build_action)

    built_unit = game.state.get_unit((0, 0), owner='O')

    assert built_unit is not None
    assert built_unit.code is "INF"
    assert built_unit.health == built_unit.max_health
    assert built_unit.ammo == built_unit.max_ammo
    assert built_unit.fuel == built_unit.max_fuel
    assert game.state.funds["O"] == initial_funds - built_unit.cost

# Can build sea unit on port
def test_can_build_sea_on_port(generate_test_game):    
    terrain = [["OPO"]]
    game = generate_test_game(terrain=terrain)
    initial_funds = game.state.funds['O']

    build_action = ActionBuild((0, 0), "LND")
    game.execute_action(build_action)
    
    built_unit = game.state.get_unit((0, 0), owner='O')

    assert built_unit is not None
    assert built_unit.code is "LND"
    assert built_unit.health == built_unit.max_health
    assert built_unit.ammo == built_unit.max_ammo
    assert built_unit.fuel == built_unit.max_fuel
    assert game.state.funds["O"] == initial_funds - built_unit.cost

# Can build air unit on airport
def test_can_build_air_on_airport(generate_test_game):    
    terrain = [["OAP"]]
    game = generate_test_game(terrain=terrain)
    initial_funds = game.state.funds['O']

    build_action = ActionBuild((0, 0), "BCP")

    game.execute_action(build_action)

    built_unit = game.state.get_unit((0, 0), owner='O')

    assert built_unit is not None
    assert built_unit.code is "BCP"
    assert built_unit.health == built_unit.max_health
    assert built_unit.ammo == built_unit.max_ammo
    assert built_unit.fuel == built_unit.max_fuel
    assert game.state.funds["O"] == initial_funds - built_unit.cost

# Cannot build on neutral
def test_cannot_build_on_neutral(generate_test_game):
    terrain = [["NBS"]]
    
    game = generate_test_game(terrain=terrain)
    
    build_action = ActionBuild((0, 0), "INF")

    with pytest.raises(Exception):
        game.execute_action(build_action)

# Cannot build on enemy
def test_cannot_build_on_enemy(generate_test_game):
    terrain = [["BBS"]]
    
    game = generate_test_game(terrain=terrain)
    
    build_action = ActionBuild((0, 0), "INF")

    with pytest.raises(Exception):
        game.execute_action(build_action)

# Cannot build on non factory properties
def test_cannot_build_on_non_factory_properties(generate_test_game):
    terrain = [["OCT"]]
    
    game = generate_test_game(terrain=terrain)
    
    build_action = ActionBuild((0, 0), "INF")

    with pytest.raises(Exception):
        game.execute_action(build_action)

# Cannot build on regular terrain
def test_cannot_build_on_regular_terrain(generate_test_game):
    terrain = [["PLN"]]
    
    game = generate_test_game(terrain=terrain)
    
    build_action = ActionBuild((0, 0), "INF")

    with pytest.raises(Exception):
        game.execute_action(build_action)

# Cannot build while occupied
def test_cannot_build_when_occupied(generate_test_game):
    units = {(0, 0): ("INF", "O")}
    terrain = [["OBS"]]
    
    game = generate_test_game(terrain=terrain, units=units)
    
    build_action = ActionBuild((0, 0), "INF")

    with pytest.raises(Exception):
        game.execute_action(build_action)

# Cannot build if not enough funds
def test_cannot_build_if_not_enough_funds(generate_test_game):
    terrain = [["OBS"]]
    
    funds = {
        "O": 0,
        "B": 0
    }
    
    game = generate_test_game(terrain=terrain, funds=funds)
    
    build_action = ActionBuild((0, 0), "INF")

    with pytest.raises(Exception):
        game.execute_action(build_action)

# Cannot act after build
def test_cannot_act_after_build(generate_test_game):
    terrain = [["OBS", "PLN"]]
    
    game = generate_test_game(terrain=terrain)
    
    build_action = ActionBuild((0, 0), "INF")
    game.execute_action(build_action)
    move_action = ActionMoveCombineLoad(ActionMove(unit_position=(0, 0), offset=(0, 1)))

    with pytest.raises(Exception):
        game.execute_action(move_action)
