from util import calculate_damage, parse_direction
from Game.Terrain import Property, TerrainAirport, TerrainPort
from Game.MoveType import MoveType
import math

class Action:
    def __init__(self) -> None:
        self.validated = False

    def execute(self):
        if not self.validated:
            raise Exception("Action not Validated")

    def validate(self, state):
        self.validated = True
        self.state = state
        return True, ""

    def validate_and_execute(self, state):
        if self.validated:
            self.execute()
            return
            
        is_valid, invalid_reason = self.validate(state)
        if is_valid:
            self.execute()
        else:
            return invalid_reason

    def __str__(self) -> str:
        return "Do Nothing"

class ActionEnd(Action):
    def __init__(self) -> None:
        super().__init__()

    def execute(self):
        super().execute()

        if self.state.current_player == len(self.state.players) - 1:
            self.state.current_day += 1

        self.state.current_player = (self.state.current_player + 1) % len(self.state.players)

        next_player = self.state.get_current_player()

        self.daily_fuel_consumption(next_player)
        self.daily_income(next_player)
        self.daily_unit_reset(next_player)
        self.daily_unit_repair_resupply(next_player)
    
    def daily_fuel_consumption(self, player):
        for unit in self.state.get_all_units(player).values():
            unit.change_fuel(-unit.daily_fuel)

    def daily_income(self, player):
        for row in self.state.terrain:
            for terrain in row:
                if isinstance(terrain, Property) and terrain.owner == player:
                    self.state.funds[terrain.owner] += 1000

    def daily_unit_reset(self, player):
        for unit in self.state.get_all_units(player).values():
            unit.available = True
    
    def daily_unit_repair_resupply(self, player):
        for r in range(self.state.map_height):
            for c in range(self.state.map_width):
                repair = False
                terrain = self.state.get_terrain((r, c))
                unit = self.state.get_unit((r, c), owner=player)
                if unit is None:
                    continue
            
                if isinstance(terrain, Property):
                    if terrain.owner is not player:
                        continue
                    if isinstance(terrain, TerrainAirport):
                        if unit.move_type is MoveType.AIR:
                            repair = True
                    elif isinstance(terrain, TerrainPort):
                        if unit.move_type is MoveType.SEA or unit.move_type is MoveType.LANDER:
                            repair = True
                    else:
                        if unit.move_type is MoveType.BOOT or unit.move_type is MoveType.FOOT or unit.move_type is MoveType.PIPE or unit.move_type is MoveType.THREADS or unit.move_type is MoveType.TIRES:
                            repair = True

                if repair:
                    unit.change_ammo(unit.max_ammo)
                    unit.change_fuel(unit.max_fuel)

                    repair_amount = max(0, min(2, 10 - unit.get_display_health()))
                    cost = (repair_amount / 10) * unit.cost
                    if self.state.funds[player] < cost:
                        return

                    self.state.funds[player] -= cost
                    unit.change_health(repair_amount * 10)
    
    def __str__(self) -> str:
        return "End Turn"

class ActionMove(Action):
    def __init__(self, unit_position, offset):
        super().__init__()

        self.unit_position = unit_position
        self.offset = offset
        self.destination = (self.unit_position[0] + self.offset[0], self.unit_position[1] + self.offset[1])

    def validate(self, state):
        self.owner = state.get_current_player()
        self.unit_to_move = state.get_unit(self.unit_position, owner=self.owner)

        if self.unit_to_move is None:
            return False, f"No unit belonging to {self.owner} was found at (r:{self.unit_position[0]}, c:{self.unit_position[1]})"

        if not self.unit_to_move.available:
            return False, "Unit is not available"
        
        if self.destination[0] < 0 or self.destination[0] >= state.map_height or self.destination[1] < 0 or self.destination[1] >= state.map_width:
            return False, f"Destination {self.destination} is out of bounds"

        if self.offset[0] == 0 and self.offset[1] == 0:
            self.fuel_cost = 0
        else:
            self.fuel_cost = state.get_movement_cost(self.unit_position, self.destination, self.unit_to_move)

            if self.fuel_cost > self.unit_to_move.move:
                return False, f"Movement cost {self.fuel_cost} exceeded unit move range {self.unit_to_move.move}"

            if self.fuel_cost > self.unit_to_move.fuel:
                return False, "Not enough fuel"

        return super().validate(state)

    def execute(self):
        super().execute()

        self.unit_to_move.change_fuel(-self.fuel_cost)

        if self.unit_position != self.destination:
            self.state.remove_unit(self.unit_position)

            # Reset property capture if moving away from it
            self.start_terrain = self.state.get_terrain(self.unit_position)
            if self.unit_to_move.can_capture and isinstance(self.start_terrain, Property):
                self.start_terrain.change_capture(self.start_terrain.owner, 20)
        
        self.state.set_unit(self.unit_to_move, self.destination)
    
    def __str__(self) -> str:
        return f"Move unit at {self.unit_position} to {self.destination}"

class ActionMoveCombineLoad(Action):
    def __init__(self, move_action):
        super().__init__()

        self.move_action = move_action
        self.is_combine = False
        self.is_load = False
        self.destination = self.move_action.destination

    def validate(self, state):
        if not self.move_action.validated:
            can_move, cannot_move_reason = self.move_action.validate(state)
            if not can_move:
                return False, cannot_move_reason

        self.owner = self.move_action.owner
        self.unit_to_move = self.move_action.unit_to_move
        #Check for combine and load
        self.unit_at_destination = state.get_unit(self.move_action.destination)
        if self.unit_at_destination is not None:
            if self.unit_at_destination.owner != self.owner:
                return False, "Destination is occupied by enemy unit"
            else:
                if type(self.unit_to_move) == type(self.unit_at_destination):
                    if self.unit_at_destination.get_display_health() == 10:
                        return False, "Cannot combine with full health unit"
                    if self.unit_at_destination is self.unit_to_move:
                        return False, "Cannot combine with self"
                    
                    self.is_combine = True        
                else:
                    if self.unit_at_destination.can_load(self.unit_to_move):
                        self.is_load = True
                    else:
                        return False, f"Cannot load {self.unit_to_move} into {self.unit_at_destination}"

        return super().validate(state)

    def execute(self):
        self.move_action.execute()
        # super().execute()
        
        if self.is_combine:
            self.excess_health = self.unit_at_destination.combine_with(self.unit_to_move)
            self.state.funds[self.owner] += (self.excess_health / 10) * self.unit_to_move.cost
            self.state.set_unit(self.unit_at_destination, self.destination)
            self.unit_at_destination.available = False
        elif self.is_load:
            self.unit_at_destination.load(self.unit_to_move)
            self.unit_to_move.available = False
            self.state.set_unit(self.unit_at_destination, self.destination)
        
        self.unit_to_move.available = False
    
    def __str__(self) -> str:
        combine_or_load = ""
        if self.is_combine:
            combine_or_load = "then combine"
        elif self.is_load:
            combine_or_load = "then load"

        return f"{str(self.move_action)} {combine_or_load}"

class ActionAttack(Action):
    def __init__(self, move_action, attack_offset) -> None:
        super().__init__()
        self.move_action = move_action
        self.unit_position = self.move_action.unit_position
        self.destination = self.move_action.destination
        self.attack_offset = attack_offset
        self.attack_target = (self.destination[0] + self.attack_offset[0], self.destination[1] + self.attack_offset[1])

        self.can_counterattack = False

    def validate(self, state):
        if not self.move_action.validated:
            can_move, cannot_move_reason = self.move_action.validate(state)
            if not can_move:
                return False, cannot_move_reason

        self.owner = self.move_action.owner
        self.attacking_unit = self.move_action.unit_to_move
        
        self.distance = abs(self.attack_target[0] - self.destination[0]) + abs(self.attack_target[1] - self.destination[1])
        if self.distance not in self.attacking_unit.range:
            return False, f"Target distance {self.distance} not in range for {self.attacking_unit} with range {self.attacking_unit.range}"

        self.defending_unit = state.get_unit(self.attack_target)
        if self.defending_unit is None:
            return False, f"No unit to attack at (r:{self.attack_target[0]}, c:{self.attack_target[1]})"

        if self.defending_unit.owner is self.owner:
            return False, "Cannot attack own unit"

        if type(self.defending_unit) not in self.attacking_unit.attack_table:
            return False, f"{self.defending_unit} cannot attack {self.attacking_unit}"
        
        self.attacker_ammo_used = self.attacking_unit.attack_table.get(type(self.defending_unit), ())[1]
        if self.attacking_unit.ammo - self.attacker_ammo_used < 0:
            return False, "Not enough ammo"

        unit_at_destination = state.get_unit(self.destination)
        if unit_at_destination is not None and unit_at_destination is not self.attacking_unit:
            return False, "Destination is occupied"

        return super().validate(state)
    
    def execute(self):
        # super().execute()
        self.move_action.execute()

        self.attacking_co = self.state.co[self.owner]
        self.defending_co = self.state.co[self.defending_unit.owner]
        self.attacking_terrain = self.state.get_terrain(self.unit_position)
        self.defending_terrain = self.state.get_terrain(self.attack_target)

        damage = calculate_damage(self.attacking_co, self.attacking_unit, self.defending_co, self.defending_unit, self.defending_terrain)
        
        self.attacking_unit.change_ammo(-self.attacker_ammo_used)
        self.defending_unit.change_health(-damage)
        if self.defending_unit.health <= 0:
            self.state.remove_unit(self.attack_target)
            if self.defending_unit.can_capture and isinstance(self.defending_terrain, Property):
                self.defending_terrain.change_capture(self.defending_terrain.owner, 20)

        self.attacking_unit.available = False

    def __str__(self) -> str:
        return f"{super().__str__()} then attack unit at {self.attack_target}"

class ActionDirectAttack(ActionAttack):
    def validate(self, state):
        can_move, cannot_move_reason = super().validate(state)
        self.validated = False
        if not can_move:
            return False, cannot_move_reason

        if self.distance != 1:
            return False, f"Target distance {self.distance} not valid for direct attack"

        if type(self.attacking_unit) in self.defending_unit.attack_table:
            self.defender_ammo_used = self.attacking_unit.attack_table.get(type(self.defending_unit), ())[1]
            if self.distance == 1 and 1 in self.defending_unit.range and self.defending_unit.ammo - self.defender_ammo_used >= 0:
                self.can_counterattack = True
        
        return True, ""

    def execute(self):
        super().execute()

        if self.can_counterattack:
            counterattack = calculate_damage(self.defending_co, self.defending_unit, self.attacking_co, self.attacking_unit, self.attacking_terrain)
            self.defending_unit.change_ammo(-self.defender_ammo_used)
            self.attacking_unit.change_health(-counterattack)
            if self.attacking_unit.health <= 0:
                self.state.remove_unit(self.unit_position)
                if self.attacking_unit.can_capture and isinstance(self.attacking_unit, Property):
                    self.attacking_unit.change_capture(self.attacking_unit.owner, 20)

class ActionIndirectAttack(ActionAttack):
    def __init__(self, unit_position, attack_offset) -> None:
        super().__init__(ActionMove(unit_position, (0, 0)), attack_offset)

    def validate(self, state):
        can_move, cannot_move_reason = super().validate(state)
        self.validated = False
        if not can_move:
            return False, cannot_move_reason

        if self.distance < 2:
            return False, f"Target distance {self.distance} not valid for indirect attack"
        
        if self.unit_position != self.destination and self.distance > 1:
            return False, f"Cannot move and indirect attack"

        return True, ""

class ActionCapture(Action):
    def __init__(self, move_action) -> None:
        super().__init__()
        self.move_action = move_action
        self.destination = self.move_action.destination
        self.capture_target = self.destination

    def validate(self, state):
        if not self.move_action.validated:
            can_move, cannot_move_reason = self.move_action.validate(state)
            if not can_move:
                return False, cannot_move_reason

        self.owner = self.move_action.owner
        self.capturing_unit = self.move_action.unit_to_move

        unit_at_destination = state.get_unit(self.destination)
        if unit_at_destination is not None and unit_at_destination is not self.capturing_unit:
            return False, "Destination is occupied"

        if not self.capturing_unit.can_capture:
            return False, f"{self.capturing_unit} cannot capture properties"
        
        self.property = state.get_property(self.capture_target)
        if self.property is None:
            return False, f"No property belonging to {self.owner} was found at {self.capture_target}"
        if self.property.owner is self.owner:
            return False, "Cannot capture own property"

        return super().validate(state)
    
    def execute(self):
        self.move_action.execute()
        
        self.property.change_capture(self.owner, -self.capturing_unit.get_display_health())
        self.capturing_unit.available = False

    def __str__(self) -> str:
        return f"{super().__str__()} then capture"

class ActionBuild(Action):
    def __init__(self, property_position, unit_code) -> None:
        super().__init__()

        self.property_position = property_position
        self.unit_code = unit_code

    def validate(self, state):
        self.owner = state.get_current_player()
        property = state.get_property(self.property_position, owner=self.owner)
        if property is None:
            return False, f"No property owned by {self.owner} found at (r:{self.property_position[0]}, c:{self.property_position[1]})"
        
        self.new_unit = state.unit_library.create(self.unit_code, self.owner)
        if state.funds[self.owner] < self.new_unit.cost:
            return False, "Cannot afford to build"

        if type(self.new_unit) not in property.buildables:
            return False, f"{property} cannot build {self.unit_code}"

        unit_at_position = state.get_unit(self.property_position)
        if unit_at_position:
            return False, "Property is already occupied"

        return super().validate(state)

    def execute(self):
        super().execute()

        self.state.set_unit(self.new_unit, self.property_position)
        self.state.funds[self.owner] -= self.new_unit.cost
        self.state.unit_built[self.owner] = True
        self.new_unit.available = False

    def __str__(self) -> str:
        return "Build {} at {}".format(self.unit_code, self.property_position)

class ActionRepair(Action):
    def __init__(self, move_action, repair_offset) -> None:
        super().__init__()
        self.move_action = move_action
        self.unit_position = self.move_action.unit_position
        self.destination = self.move_action.destination
        self.repair_offset = repair_offset
        self.repair_target = (self.destination[0] + repair_offset[0], self.destination[1] + repair_offset[1])

    def validate(self, state):
        if not self.move_action.validated:
            can_move, cannot_move_reason = self.move_action.validate(state)
            if not can_move:
                return False, cannot_move_reason

        self.owner = self.move_action.owner
        self.repairing_unit = self.move_action.unit_to_move

        if abs(self.repair_offset[0]) + abs(self.repair_offset[1]) != 1:
            return False, "Invalid repair direction"

        unit_at_destination = state.get_unit(self.destination)
        if unit_at_destination is not None and unit_at_destination is not self.repairing_unit:
            return False, "Destination is occupied"

        if not self.repairing_unit.can_repair:
            return False, "{repairing_unit} cannot perform repairs"

        self.unit_to_repair = state.get_unit(self.repair_target, owner=self.owner)
        if self.unit_to_repair is None:
            return False, f"No unit belonging to {self.owner} was found at (r:{self.repair_target[0]}, c:{self.repair_target[1]})"

        self.repair_amount = min(self.repairing_unit.repair_amount, 10 - self.unit_to_repair.get_display_health())
        self.cost = (self.repair_amount / 10) * self.unit_to_repair.cost
        if state.funds[self.owner] < self.cost:
            return False, "Not enough funds"

        return super().validate(state)

    def execute(self):
        self.move_action.execute()

        self.state.funds[self.owner] -= self.cost
        self.unit_to_repair.change_health(self.repair_amount * 10)
        self.unit_to_repair.change_fuel(self.unit_to_repair.max_fuel)
        self.unit_to_repair.change_ammo(self.unit_to_repair.max_ammo)
        self.repairing_unit.available = False

    def __str__(self) -> str:
        return f"{super().__str__()} then repairs unit at {self.repair_target}"

class ActionUnload(Action):
    def __init__(self, move_action, unload_offset, idx) -> None:
        super().__init__()
        self.move_action = move_action
        self.unit_position = self.move_action.unit_position
        self.destination = self.move_action.destination
        self.unload_offset = unload_offset
        self.unload_position = (self.destination[0] + unload_offset[0], self.destination[1] + unload_offset[1])
        self.idx = idx

    def validate(self, state):
        if not self.move_action.validated:
            can_move, cannot_move_reason = self.move_action.validate(state)
            if not can_move:
                return False, cannot_move_reason

        self.unloading_unit = self.move_action.unit_to_move

        if abs(self.unload_offset[0]) + abs(self.unload_offset[1]) != 1:
            return False, "Invalid unload direction"

        unit_at_destination = state.get_unit(self.destination)
        if unit_at_destination is not None and unit_at_destination is not self.unloading_unit:
            return False, "Destination is occupied"
        
        if not self.unloading_unit.can_unload(self.idx):
            return False, "Nothing to unload"

        distance = abs(self.destination[0] - self.unload_position[0]) + abs(self.destination[1] - self.unload_position[1])
        
        if distance > 1:
            return False, "Can only unload adjacent to the unit"

        if not self.unloading_unit.can_unload(self.idx):
            return False, "Invalid unit index"

        self.unloaded_unit = self.unloading_unit.in_load[self.idx]
        terrain = state.get_terrain(self.unload_position)
        if terrain is None:
            return False, f"{self.unload_position} is not a valid unload position"

        if terrain.get_move_cost(self.unloaded_unit.move_type) == 0:
            return False, f"{self.unloaded_unit} cannot be placed on {terrain}"

        own_terrain = state.get_terrain(self.destination)
        if own_terrain.get_move_cost(self.unloaded_unit.move_type) == 0:
            return False, f"{self.unloading_unit} cannot unload while on {terrain}"

        unit_at_position = state.get_unit(self.unload_position)
        if unit_at_position:
            return False, "Already something there"

        return super().validate(state)

    def execute(self):
        super().execute()
        self.move_action.execute()

        self.unloading_unit.unload(self.idx)
        self.state.set_unit(self.unloaded_unit, self.unload_position)
        self.unloading_unit.available = False

    def __str__(self) -> str:
        return f"{super().__str__()} then unloads {self.idx} at {self.unload_position}"

class ActionCOP(Action):
    pass

class ActionSCOP(Action):
    pass
        
