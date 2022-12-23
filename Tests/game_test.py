from Game.Game import Game
from Game.CO import BaseCO

import json

# Test map loading
def test_load_tiny_test(base_cos):
    with open('Maps/Tiny_Test.json', 'r+') as map_file:
        map_data = json.loads(map_file.read())
        specified_terrain = map_data['terrain']
        specified_units = map_data['units']
    
    game = Game.load_map(base_cos, "Maps/Tiny_Test.json")

    assert [[terrain.code.replace(".", getattr(terrain, "owner", ".")) for terrain in row] for row in game.state.terrain] == specified_terrain
    
    for owner, unit_list in specified_units.items():
        for unit in unit_list:
            specified_unit_code = unit['code']
            specified_position = (unit['row'], unit['col'])
            print(specified_position, owner)
            assert game.state.get_unit(specified_position, owner=owner) is not None
            assert game.state.get_unit(specified_position, owner=owner).code == specified_unit_code
