from Game.Terrain import Property, TerrainHeadquarters
from Game.Unit import UnitLibrary, standard_units
from Game.MoveType import MoveType
import math
import numpy as np
import queue
from scipy.sparse.csgraph import shortest_path
'''
A data class
'''
class State:
    def __init__(self, co=None, terrain=[[]], units={}, funds=None, first_player=0):
        self.co = co
        self.terrain = terrain
        self.unit_library = UnitLibrary(standard_units)

        self.map_height = len(terrain)
        self.map_width = len(terrain[0])

        self.units = units

        self.players = list(self.co.keys())

        self.current_player = first_player
        
        self.current_day = 1

        self.properties = {(r, c): self.terrain[r][c] for r in range(self.map_height) for c in range(self.map_width) if isinstance(self.terrain[r][c], Property)}

        self.funds = funds or {player: 1000 * len(self.get_all_properties(player)) if player == self.get_current_player() else 0 for player in self.players}

        self.unit_built = {player: len(self.get_all_units(owner=player)) > 0 for player in self.players}
        self.has_hq = {player: any([isinstance(property, TerrainHeadquarters) for property in self.get_all_properties(owner=player).values()]) for player in self.players}

        self._movement_costs = {}

        self._terrain_adjacency_matrix = {
            move_type: np.full((self.map_height * self.map_width, self.map_height * self.map_width), 100) for move_type in MoveType
        }
        self._terrain_movement_costs = {}

        for move_type in MoveType:
            for r in range(self.map_height):
                for c in range(self.map_width):
                    source_idx = r * self.map_width + c
                    self._terrain_adjacency_matrix[move_type][source_idx][source_idx] = 0

                    targets = [
                        (r + 1, c),
                        (r - 1, c),
                        (r, c + 1),
                        (r, c - 1)
                    ]

                    for target in targets:
                        target_idx = target[0] * self.map_width + target[1]
                        
                        terrain = self.get_terrain(target)
                        if terrain is None:
                            continue

                        cost = terrain.get_move_cost(move_type)
                        if cost == 0:
                            continue

                        self._terrain_adjacency_matrix[move_type][source_idx][target_idx] = cost
            self._terrain_movement_costs[move_type] = shortest_path(self._terrain_adjacency_matrix[move_type])
        
        self.update_movement_cost()

    def get_unit(self, unit_position, owner=None):
        if unit_position in self.units:
            unit = self.units[unit_position]
            return unit if owner is None or unit.owner is owner else None
        else:
            return None

    def get_all_units(self, owner=None):
        if owner is None:
            return self.units
        else:
            return {position: unit for position, unit in self.units.items() if unit.owner is owner}

    def remove_unit(self, unit_position):
        if unit_position not in self.units:
            return

        del self.units[unit_position]
    
    def set_unit(self, unit, position):
        self.units[position] = unit
    
    def add_unit(self, position, unit_code, owner):
        self.units[position] = self.unit_library.create(unit_code, owner)

    def get_current_player(self):
        return self.players[self.current_player]

    def get_terrain(self, position):
        if position[0] >= self.map_height or position[1] >= self.map_width or position[0] < 0 or position[1] < 0:
            return None
    
        return self.terrain[position[0]][position[1]]

    def get_property(self, position, owner=None):
        if position in self.properties:
            property = self.properties[position]
            return property if owner is None or property.owner is owner else None
        else:
            return None
    
    def get_all_properties(self, owner=None):
        if owner is None:
            return self.properties
        else:
            return {position: property for position, property in self.properties.items() if property.owner is owner}

    def set_terrain(self, terrain, position):
        self.terrain[position[0]][position[1]] = terrain

    def check_winner(self):
        remaining_players = set(self.players)
        for player in self.players:
            if self.has_hq[player] and not any([isinstance(property, TerrainHeadquarters) for property in self.get_all_properties(owner=player).values()]):
                remaining_players.discard(player)
                continue
            if self.unit_built[player] and len(self.get_all_units(owner=player)) == 0:
                remaining_players.discard(player)
                continue
        
        return remaining_players.pop() if len(remaining_players) == 1 else None
    
    def get_player_stats(self, player):
        stats = {}
        player_units = self.get_all_units(player)
        # Unit count
        stats['unit_count'] = len(player_units)
        # Army value
        stats['army_value'] = sum([unit.cost * unit.get_display_health() / 10 for unit in player_units.values()])
        # Income
        stats['income'] = len(self.get_all_properties(player)) * 1000
        # Funds
        stats['funds'] = self.funds[player]
        return stats
    
    def text_display(self):
        unit_grid  = [[None for _ in range(self.map_width)] for _ in range(self.map_height)]

        for position, unit in self.get_all_units().items():
            unit_grid[position[0]][position[1]] = (unit.owner, unit)

        map_lines = []

        top_number_line = []
        for c in range(self.map_width):
            top_number_line.append(f"  {c}  ")
        map_lines.append("  |{}|".format(" ".join(top_number_line)))

        for r in range(self.map_height):
            unit_line = []
            for c in range(self.map_width):
                unit_code = "     " if unit_grid[r][c] is None else "{owner} {type_code}".format(owner=unit_grid[r][c][0], type_code=unit_grid[r][c][1])
                unit_line.append(unit_code)
            map_lines.append("  |{}|".format("|".join(unit_line)))

            unit_status_line = []
            for c in range(self.map_width):
                unit_status = "     " if unit_grid[r][c] is None else "{health}{fuel:02}{ammo:02}".format(health="-" if unit_grid[r][c][1].health > 90 else unit_grid[r][c][1].get_display_health(), fuel=unit_grid[r][c][1].fuel, ammo=unit_grid[r][c][1].ammo)
                unit_status_line.append(unit_status)
                if unit_grid[r][c] is not None and unit_grid[r][c][1].get_display_health() == 0:
                    raise Exception(f"OOPS unit: {unit_grid[r][c][1]}, owner: {unit_grid[r][c][0]}, health: {unit_grid[r][c][1].health}")
            map_lines.append("{} |{}|".format(r, "|".join(unit_status_line)))

            terrain_line = []
            for c in range(self.map_width):
                terrain_line.append(" {} ".format(self.get_terrain((r, c))))
            map_lines.append("  |{}|".format("|".join(terrain_line)))
            
        return "\n".join(map_lines)

    # def update_movement_cost(self):
    #     current_player = self.get_current_player()
    #     available_move_types = set()
            
    #     occupancy_grid = np.full((self.map_height * self.map_width, self.map_height * self.map_width), 0)
    #     for position, unit in self.get_all_units().items():
    #         if unit.owner != current_player:
    #             occupancy_grid[:,position[0] * self.map_width + position[1]] = 100
    #         else:
    #             available_move_types.add(unit.move_type)

    #     for move_type in available_move_types:
    #         graph = occupancy_grid + self._terrain_movement_costs[move_type]
    #         self._movement_costs[move_type] = shortest_path(graph)

    
    def update_movement_cost(self):
        current_player = self.get_current_player()
        occupied = {position for position, unit in self.get_all_units().items() if unit.owner != current_player}
            
        self._unblocked_spaces = {}
        for position, unit in self.get_all_units(owner=current_player).items():
            self._unblocked_spaces[position] = self.get_unblocked_spaces(position, unit, occupied)
        
    
    def get_unblocked_spaces(self, start, unit, occupied):
        visited = set()
        pending = [start]
        while len(pending) > 0:
            current = pending.pop()
            terrain = self.terrain[current[0]][current[1]]
            
            if current in visited or current in occupied or terrain.get_move_cost(unit.move_type) == 0:
                continue
            visited.add(current)

            distance = abs(current[0] - start[0]) + abs(current[1] - start[1])
            if distance + 1 > unit.move:
                continue
            above = current[0] + 1
            if above < self.map_height:
                pending.append((above, current[1]))
            below = current[0] - 1
            if below >= 0:
                pending.append((below, current[1]))
            right = current[1] + 1
            if right < self.map_width:
                pending.append((current[0], right))
            left = current[1] - 1
            if left >= 0:
                pending.append((current[0], current[1]-1))

        return visited

    def get_movement_cost(self, start, end, unit):
        start_id = start[0] * self.map_width + start[1]
        end_id = end[0] * self.map_width + end[1]

        if end in self._unblocked_spaces[start]:
            return int(self._terrain_movement_costs[unit.move_type][start_id][end_id])
        else:
            return 100
    
    def get_shortest_path(self, start, end, unit):
        start_id = start[0] * self.map_width + start[1]
        end_id = end[0] * self.map_width + end[1]

        current_player = self.get_current_player()
            
        occupancy_grid = np.full((self.map_height * self.map_width, self.map_height * self.map_width), 0)
        for position, other_unit in self.get_all_units().items():
            if other_unit.owner != current_player:
                occupancy_grid[:,position[0] * self.map_width + position[1]] = 100
        
        graph = occupancy_grid + self._terrain_adjacency_matrix[unit.move_type]
        movement_costs, predecessors = shortest_path(graph, indices=start_id, return_predecessors=True)

        path = []
        cur = end_id
        while cur != -9999:
            path.append(int(cur))
            cur = predecessors[cur]

        path.reverse()
        return path

    def __str__(self):
        return self.text_display()