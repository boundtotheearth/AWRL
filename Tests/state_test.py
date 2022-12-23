from Game.State import State
from Game.CO import BaseCO
from Game.Terrain import TerrainLibrary, standard_terrain, Property
from Game.Unit import UnitLibrary, standard_units
from Game.Action import ActionEnd

import pytest
import math
import copy

# Can get unit for any owner
def test_get_unit_no_owner(generate_test_game):
    terrain = [
        ["PLN", "PLN", "PLN", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "PLN"],
        ["PLN", "SEA", "PLN", "PLN", "SEA"],
        ["PLN", "PIP", "SEA", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "SEA"]
    ]

    units_codes = [
        ["INF", "MEC", "REC", "TCP", "APC"],
        ["ATY", "TNK", "BLB", "AAR", "BCP"],
        ["MIS", "LND", "ROK", "MTK", "CRU"],
        ["FGT", "PRN", "SUB", "NTK", "BMB"],
        ["STH", "BBB", "BSP", "MGT", "CAR"]
    ]
    units = {(r, c): (units_codes[r][c], 'O') for r in range(len(units_codes)) for c in range(len(units_codes[0]))}

    game = generate_test_game(terrain=terrain, units=units)

    for r in range(len(units_codes)):
        for c in range(len(units_codes[0])):
            created_unit = game.state.get_unit((r, c))
            created_unit_code = created_unit.code

            assert created_unit_code == units_codes[r][c]

# Can get unit for specific owner
def test_get_unit_with_owner(generate_test_game):
    terrain = [
        ["PLN", "PLN", "PLN", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "PLN"],
        ["PLN", "SEA", "PLN", "PLN", "SEA"],
        ["PLN", "PIP", "SEA", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "SEA"]
    ]

    units_codes = [
        ["INF", "MEC", "REC", "TCP", "APC"],
        ["ATY", "TNK", "BLB", "AAR", "BCP"],
        ["MIS", "LND", "ROK", "MTK", "CRU"],
        ["FGT", "PRN", "SUB", "NTK", "BMB"],
        ["STH", "BBB", "BSP", "MGT", "CAR"]
    ]

    units = {(r, c): (units_codes[r][c], 'B') for r in range(len(units_codes)) for c in range(len(units_codes[0]))}

    game = generate_test_game(terrain=terrain, units=units)

    for r in range(len(units_codes)):
        for c in range(len(units_codes[0])):
            created_unit = game.state.get_unit((r, c), 'B')
            created_unit_code = created_unit.code

            assert created_unit_code == units_codes[r][c]

# Can get all units for any owner
def test_get_all_units_no_owner(generate_test_game):
    terrain = [
        ["PLN", "PLN", "PLN", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "PLN"],
        ["PLN", "SEA", "PLN", "PLN", "SEA"],
        ["PLN", "PIP", "SEA", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "SEA"]
    ]

    units_codes = [
        ["INF", "MEC", "REC", "TCP", "APC"],
        ["ATY", "TNK", "BLB", "AAR", "BCP"],
        ["MIS", "LND", "ROK", "MTK", "CRU"],
        ["FGT", "PRN", "SUB", "NTK", "BMB"],
        ["STH", "BBB", "BSP", "MGT", "CAR"]
    ]

    units = {(r, c): (units_codes[r][c], 'O' if r % 2 == 0 else 'B') for r in range(len(units_codes)) for c in range(len(units_codes[0]))}

    game = generate_test_game(terrain=terrain, units=units)

    created_units = {position: (unit.code, unit.owner) for position, unit in game.state.get_all_units().items()}
    assert created_units == units

# Can get all units for specific owner
def test_get_all_units_with_owner(generate_test_game):
    terrain = [
        ["PLN", "PLN", "PLN", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "PLN"],
        ["PLN", "SEA", "PLN", "PLN", "SEA"],
        ["PLN", "PIP", "SEA", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "SEA"]
    ]

    units_codes = [
        ["INF", "MEC", "REC", "TCP", "APC"],
        ["ATY", "TNK", "BLB", "AAR", "BCP"],
        ["MIS", "LND", "ROK", "MTK", "CRU"],
        ["FGT", "PRN", "SUB", "NTK", "BMB"],
        ["STH", "BBB", "BSP", "MGT", "CAR"]
    ]

    units = {(r, c): (units_codes[r][c], 'O' if r % 2 == 0 else 'B') for r in range(len(units_codes)) for c in range(len(units_codes[0]))}

    game = generate_test_game(terrain=terrain, units=units)

    created_units = {position: (unit.code, unit.owner) for position, unit in game.state.get_all_units('O').items()}
    assert created_units == {position: unit for position, unit in units.items() if unit[1] == 'O'}

# Can remove units at position
def test_remove_unit_at_position(generate_test_game):
    terrain = [
        ["PLN", "PLN", "PLN", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "PLN"],
        ["PLN", "SEA", "PLN", "PLN", "SEA"],
        ["PLN", "PIP", "SEA", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "SEA"]
    ]

    units_codes = [
        ["INF", "MEC", "REC", "TCP", "APC"],
        ["ATY", "TNK", "BLB", "AAR", "BCP"],
        ["MIS", "LND", "ROK", "MTK", "CRU"],
        ["FGT", "PRN", "SUB", "NTK", "BMB"],
        ["STH", "BBB", "BSP", "MGT", "CAR"]
    ]

    units = {(r, c): (units_codes[r][c], 'O' if r % 2 == 0 else 'B') for r in range(len(units_codes)) for c in range(len(units_codes[0]))}

    game = generate_test_game(terrain=terrain, units=units)

    expected_units = copy.deepcopy(units)

    positions_to_remove = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
    for position in positions_to_remove:
        game.state.remove_unit(position)
        del expected_units[position]
        
    created_units = game.state.get_all_units()
    assert {position: unit.code for position, unit in created_units.items()} == {position: unit[0] for position, unit in expected_units.items()}

# Can place units at position
def test_set_unit_at_posiiton(generate_test_game, unit_library):
    terrain = [
        ["PLN", "PLN", "PLN", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "PLN"],
        ["PLN", "SEA", "PLN", "PLN", "SEA"],
        ["PLN", "PIP", "SEA", "PLN", "PLN"],
        ["PLN", "PLN", "SEA", "PLN", "SEA"]
    ]

    game = generate_test_game(terrain=terrain)

    units_to_set = {
        (1, 0): ("MEC", "O"),
        (1, 1): ("TNK", "O"),
        (1, 2): ("LND", "O"),
        (1, 3): ("PRN", "O"),
        (1, 4): ("BBB", "O"),
    }

    for position, unit in units_to_set.items():
        game.state.set_unit(unit_library.create(unit[0], unit[1]), position)

    created_units = game.state.get_all_units()
    assert units_to_set == {position: (unit.code, unit.owner) for position, unit in created_units.items()}

# Can get the current player
def test_get_current_player(generate_test_game):
    game = generate_test_game()
    
    game.execute_action(ActionEnd())

    assert game.state.get_current_player() == 'B'

    game.execute_action(ActionEnd())

    assert game.state.get_current_player() == 'O'

# Can get terrain at position
def test_get_terrain_at_position(generate_test_game):
    terrain = [
        ['PLN', 'MTN', 'WOD', 'RVR', 'ROD'],
        ['SEA', 'SHL', 'REF', 'PIP', 'NCT'],
        ['BAP', 'BPO', 'BLB', 'BCM', 'PLN']
    ]

    game = generate_test_game(terrain=terrain)

    for r in range(len(terrain)):
        for c in range(len(terrain[0])):
            created_terrain = game.state.get_terrain((r, c))
            created_terrain_code = created_terrain.code
            if isinstance(created_terrain, Property):
                created_terrain_code = created_terrain_code.replace(".", created_terrain.owner)

            assert created_terrain_code == terrain[r][c]

# Get terrain also returns properties
def test_get_terrain_returns_properties(generate_test_game):
    terrain = [
        ['NBS', 'NAP', 'NPO', 'NLB', 'NCM'],
        ['OCT', 'OHQ', 'OBS', 'OAP', 'OPO'],
        ['OLB', 'OCM', 'BCT', 'BHQ', 'BBS'],
        ['BAP', 'BPO', 'BLB', 'BCM', 'PLN']
    ]

    game = generate_test_game(terrain=terrain)

    for r in range(len(terrain)):
        for c in range(len(terrain[0])):
            created_terrain = game.state.get_terrain((r, c))
            created_terrain_code = created_terrain.code
            if isinstance(created_terrain, Property):
                created_terrain_code = created_terrain_code.replace(".", created_terrain.owner)

            assert created_terrain_code == terrain[r][c]

# Can get property at position for any owner
def test_get_property_at_position_no_owner(generate_test_game):
    terrain = [
        ['NBS', 'NAP', 'NPO', 'NLB', 'NCM'],
        ['OCT', 'OHQ', 'OBS', 'OAP', 'OPO'],
        ['OLB', 'OCM', 'BCT', 'BHQ', 'BBS'],
        ['BAP', 'BPO', 'BLB', 'BCM', 'BCM']
    ]

    game = generate_test_game(terrain=terrain)
    print(game.state.terrain)

    for r in range(len(terrain)):
        for c in range(len(terrain[0])):
            created_property = game.state.get_property((r, c))
            create_property_code = created_property.code.replace(".", created_property.owner)
            assert create_property_code == terrain[r][c]

# Can get property at position for specified owner
def test_get_property_at_position_with_owner(generate_test_game):
    terrain = [
        ['NBS', 'NAP', 'NPO', 'NLB', 'NCM'],
        ['OCT', 'OHQ', 'OBS', 'OAP', 'OPO'],
        ['OLB', 'OCM', 'BCT', 'BHQ', 'BBS'],
        ['BAP', 'BPO', 'BLB', 'BCM', 'PLN']
    ]

    game = generate_test_game(terrain=terrain)

    for r in range(len(terrain)):
        for c in range(len(terrain[0])):
            created_property = game.state.get_property((r, c), 'O')
            if terrain[r][c][0] == 'O':
                assert created_property is not None

# Get property does not return normal terrain
def test_get_property_does_not_return_normal_terrain(generate_test_game):
    terrain = [
        ['PLN', 'MTN', 'WOD', 'RVR', 'ROD'],
        ['SEA', 'SHL', 'REF', 'PIP', 'PLN']
    ]

    game = generate_test_game(terrain=terrain)

    for r in range(len(terrain)):
        for c in range(len(terrain[0])):
            assert game.state.get_property((r, c)) is None

# Can set terrain at position
def test_set_terrain_at_position(generate_test_game):
    initial_terrain = [
        ['PLN', 'PLN', 'PLN', 'PLN', 'PLN'],
        ['PLN', 'PLN', 'PLN', 'PLN', 'PLN'],
        ['PLN', 'PLN', 'PLN', 'PLN', 'PLN'],
        ['PLN', 'PLN', 'PLN', 'PLN', 'PLN'],
        ['PLN', 'PLN', 'PLN', 'PLN', 'PLN'],
        ['PLN', 'PLN', 'PLN', 'PLN', 'PLN']
    ]

    new_terrain = [
        ['PLN', 'MTN', 'WOD', 'RVR', 'ROD'],
        ['SEA', 'SHL', 'REF', 'PIP', 'NCT'],
        ['NBS', 'NAP', 'NPO', 'NLB', 'NCM'],
        ['OCT', 'OHQ', 'OBS', 'OAP', 'OPO'],
        ['OLB', 'OCM', 'BCT', 'BHQ', 'BBS'],
        ['BAP', 'BPO', 'BLB', 'BCM', 'PLN']
    ]
    
    game = generate_test_game(terrain=initial_terrain)

    for r in range(len(new_terrain)):
       for c in range(len(new_terrain[0])):
            game.state.set_terrain(new_terrain[r][c], (r, c))

    for r in range(len(new_terrain)):
        for c in range(len(new_terrain[0])):
            assert game.state.get_terrain((r, c)) == new_terrain[r][c]

# TODO: Can check if there is a winner

# TODO: Can display state as text
