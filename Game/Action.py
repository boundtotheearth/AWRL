from util import calculate_damage, parse_direction
from Game.Terrain import Property, TerrainAirport, TerrainPort, TerrainCommTower
from Game.MoveType import MoveType
import math

class Action:
    def __init__(self) -> None:
        self.validated = False
        self.invalid_message = "No Message"

    def execute(self):
        if not self.validated:
            raise Exception("Action not Validated")

    def validate(self, state):
        self.validated = True
        self.state = state
        return True
    
    def invalidate(self):
        self.validated = False
        self.state = None

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

        self.state.update_movement_cost()
        self.daily_fuel_consumption(next_player)
        self.daily_income(next_player)
        self.daily_unit_reset(next_player)
        self.daily_unit_repair_resupply(next_player)
        self.reset_powers(next_player)
    
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
    
    def reset_powers(self, player):
        co = self.state.get_co(player)
        if co.cop_applied:
            co.reset_cop(self.state)
        if co.scop_applied:
            co.reset_scop(self.state)

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
            self.invalid_message = f"No unit belonging to {self.owner} was found at (r:{self.unit_position[0]}, c:{self.unit_position[1]})"
            return False

        self.fuel_cost = state.get_movement_cost(self.unit_position, self.destination, self.unit_to_move)

        if self.fuel_cost > self.unit_to_move.move:
            self.invalid_message = f"Movement cost {self.fuel_cost} exceeded unit move range {self.unit_to_move.move}"
            return False

        if self.fuel_cost > self.unit_to_move.fuel:
            self.invalid_message = "Not enough fuel"
            return False
        
        if self.destination[0] < 0 or self.destination[0] >= state.map_height or self.destination[1] < 0 or self.destination[1] >= state.map_width:
            self.invalid_message = f"Destination {self.destination} is out of bounds"
            return False
        
        if not self.unit_to_move.available:
            self.invalid_message = "Unit is not available"
            return False

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
            can_move = self.move_action.validate(state)
            if not can_move:
                self.invalid_message = self.move_action.invalid_message
                return False

        self.owner = self.move_action.owner
        self.unit_to_move = self.move_action.unit_to_move
        #Check for combine and load
        self.unit_at_destination = state.get_unit(self.move_action.destination)
        if self.unit_at_destination is not None:
            if self.unit_at_destination.owner != self.owner:
                self.invalid_message = "Destination is occupied by enemy unit"
                return False
            else:
                if type(self.unit_to_move) == type(self.unit_at_destination):
                    if self.unit_at_destination.get_display_health() == 10:
                        self.invalid_message = "Cannot combine with full health unit"
                        return False
                    if self.unit_at_destination is self.unit_to_move:
                        self.invalid_message = "Cannot combine with self"
                        return False
                    
                    self.is_combine = True        
                else:
                    if self.unit_at_destination.can_load(self.unit_to_move):
                        self.is_load = True
                    else:
                        self.invalid_message = f"Cannot load {self.unit_to_move} into {self.unit_at_destination}"
                        return False

        return super().validate(state)

    def execute(self):
        self.move_action.execute()
        
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
            can_move = self.move_action.validate(state)
            if not can_move:
                self.invalid_message = self.move_action.invalid_message
                return False

        self.owner = self.move_action.owner
        self.attacking_unit = self.move_action.unit_to_move
        
        self.distance = abs(self.attack_target[0] - self.destination[0]) + abs(self.attack_target[1] - self.destination[1])
        if self.distance not in self.attacking_unit.range:
            self.invalid_message = f"Target distance {self.distance} not in range for {self.attacking_unit} with range {self.attacking_unit.range}"
            return False

        self.defending_unit = state.get_unit(self.attack_target)
        if self.defending_unit is None:
            self.invalid_message = f"No unit to attack at (r:{self.attack_target[0]}, c:{self.attack_target[1]})"
            return False

        if self.defending_unit.owner is self.owner:
            self.invalid_message = "Cannot attack own unit"
            return False

        if type(self.defending_unit) not in self.attacking_unit.attack_table:
            self.invalid_message = f"{self.defending_unit} cannot attack {self.attacking_unit}"
            return False
        
        self.attacker_ammo_used = self.attacking_unit.attack_table.get(type(self.defending_unit), ())[1]
        if self.attacking_unit.ammo - self.attacker_ammo_used < 0:
            self.invalid_message = "Not enough ammo"
            return False

        unit_at_destination = state.get_unit(self.destination)
        if unit_at_destination is not None and unit_at_destination is not self.attacking_unit:
            self.invalid_message = "Destination is occupied"
            return False

        return super().validate(state)
    
    def execute(self):
        self.move_action.execute()

        self.attacking_co = self.state.co[self.owner]
        self.defending_co = self.state.co[self.defending_unit.owner]
        self.attacking_terrain = self.state.get_terrain(self.unit_position)
        self.defending_terrain = self.state.get_terrain(self.attack_target)
        self.attacking_CT = 0
        self.defending_CT = 0
        for p in self.state.get_all_properties().values():
            if p.owner == self.owner:
                self.attacking_CT += 1
            elif p.owner == self.defending_unit.owner:
                self.defending_CT += 1

        damage = calculate_damage(self.attacking_co, self.attacking_unit, self.defending_co, self.defending_unit, self.defending_terrain, self.attacking_CT)
        
        self.attacking_unit.change_ammo(-self.attacker_ammo_used)
        original_health = self.defending_unit.get_display_health()
        self.defending_unit.change_health(-damage)

        health_loss = self.defending_unit.get_display_health() - original_health
        self.value_inflicted = (health_loss / 10) * self.defending_unit.cost
        self.defending_co.charge_power(-self.value_inflicted)
        self.attacking_co.charge_power(-0.5 * self.value_inflicted)

        if self.defending_unit.health <= 0:
            self.state.remove_unit(self.attack_target)
            if self.defending_unit.can_capture and isinstance(self.defending_terrain, Property):
                self.defending_terrain.change_capture(self.defending_terrain.owner, 20)
            self.state.update_movement_cost()

        self.attacking_unit.available = False

    def __str__(self) -> str:
        return f"{str(self.move_action)} then attack unit at {self.attack_target}"

class ActionDirectAttack(ActionAttack):
    def validate(self, state):
        can_move = super().validate(state)
        self.validated = False
        if not can_move:
            return False

        if self.distance != 1:
            self.invalid_message = f"Target distance {self.distance} not valid for direct attack"
            return False

        if type(self.attacking_unit) in self.defending_unit.attack_table:
            self.defender_ammo_used = self.attacking_unit.attack_table.get(type(self.defending_unit), ())[1]
            if self.distance == 1 and 1 in self.defending_unit.range and self.defending_unit.ammo - self.defender_ammo_used >= 0:
                self.can_counterattack = True
        
        return True

    def execute(self):
        super().execute()

        if self.can_counterattack:
            counterattack = calculate_damage(self.defending_co, self.defending_unit, self.attacking_co, self.attacking_unit, self.attacking_terrain, self.defending_CT)
            self.defending_unit.change_ammo(-self.defender_ammo_used)
            original_health = self.attacking_unit.get_display_health()
            self.attacking_unit.change_health(-counterattack)

            health_loss = self.attacking_unit.get_display_health() - original_health
            self.counterattack_value_inflicted = (health_loss / 10) * self.attacking_unit.cost
            self.attacking_co.charge_power(-self.counterattack_value_inflicted)
            self.defending_co.charge_power(-0.5 * self.counterattack_value_inflicted)
            
            if self.attacking_unit.health <= 0:
                self.state.remove_unit(self.destination)
                if self.attacking_unit.can_capture and isinstance(self.attacking_unit, Property):
                    self.attacking_unit.change_capture(self.attacking_unit.owner, 20)
                self.state.update_movement_cost()

class ActionIndirectAttack(ActionAttack):
    def __init__(self, unit_position, attack_offset) -> None:
        super().__init__(ActionMove(unit_position, (0, 0)), attack_offset)

    def validate(self, state):
        can_move = super().validate(state)
        self.validated = False
        if not can_move:
            return False

        if self.distance < 2:
            self.invalid_message = f"Target distance {self.distance} not valid for indirect attack"
            return False
        
        if self.unit_position != self.destination and self.distance > 1:
            self.invalid_message = f"Cannot move and indirect attack"
            return False

        return True

class ActionCapture(Action):
    def __init__(self, move_action) -> None:
        super().__init__()
        self.move_action = move_action
        self.destination = self.move_action.destination
        self.capture_target = self.destination

    def validate(self, state):
        if not self.move_action.validated:
            can_move = self.move_action.validate(state)
            if not can_move:
                self.invalid_message = self.move_action.invalid_message
                return False

        self.owner = self.move_action.owner
        self.capturing_unit = self.move_action.unit_to_move

        unit_at_destination = state.get_unit(self.destination)
        if unit_at_destination is not None and unit_at_destination is not self.capturing_unit:
            self.invalid_message = "Destination is occupied"
            return False

        if not self.capturing_unit.can_capture:
            self.invalid_message = f"{self.capturing_unit} cannot capture properties"
            return False
        
        self.property = state.get_property(self.capture_target)
        if self.property is None:
            self.invalid_message = f"No property belonging to {self.owner} was found at {self.capture_target}"
            return False
        if self.property.owner is self.owner:
            self.invalid_message = "Cannot capture own property"
            return False

        return super().validate(state)
    
    def execute(self):
        self.move_action.execute()
        
        self.property.change_capture(self.owner, -self.capturing_unit.get_display_health())
        self.capturing_unit.available = False

    def __str__(self) -> str:
        return f"{str(self.move_action)} then capture"

class ActionBuild(Action):
    def __init__(self, property_position, unit_code) -> None:
        super().__init__()

        self.property_position = property_position
        self.unit_code = unit_code

    def validate(self, state):
        self.owner = state.get_current_player()
        property = state.get_property(self.property_position, owner=self.owner)
        if property is None:
            self.invalid_message = f"No property owned by {self.owner} found at (r:{self.property_position[0]}, c:{self.property_position[1]})"
            return False
        
        self.new_unit = state.unit_library.create(self.unit_code, self.owner)
        if state.funds[self.owner] < self.new_unit.cost:
            self.invalid_message = "Cannot afford to build"
            return False

        if type(self.new_unit) not in property.buildables:
            self.invalid_message = f"{property} cannot build {self.unit_code}"
            return False

        unit_at_position = state.get_unit(self.property_position)
        if unit_at_position:
            self.invalid_message = "Property is already occupied"
            return False

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
            can_move = self.move_action.validate(state)
            if not can_move:
                self.invalid_message = self.move_action.invalid_message
                return False

        self.owner = self.move_action.owner
        self.repairing_unit = self.move_action.unit_to_move

        if abs(self.repair_offset[0]) + abs(self.repair_offset[1]) != 1:
            self.invalid_message = "Invalid repair direction"
            return False

        unit_at_destination = state.get_unit(self.destination)
        if unit_at_destination is not None and unit_at_destination is not self.repairing_unit:
            self.invalid_message = "Destination is occupied"
            return False

        if not self.repairing_unit.can_repair:
            self.invalid_message = f"{self.repairing_unit} cannot perform repairs"
            return False

        self.unit_to_repair = state.get_unit(self.repair_target, owner=self.owner)
        if self.unit_to_repair is None:
            self.invalid_message = f"No unit belonging to {self.owner} was found at (r:{self.repair_target[0]}, c:{self.repair_target[1]})"
            return False

        self.repair_amount = min(self.repairing_unit.repair_amount, 10 - self.unit_to_repair.get_display_health())
        self.cost = (self.repair_amount / 10) * self.unit_to_repair.cost
        if state.funds[self.owner] < self.cost:
            self.invalid_message = "Not enough funds"
            return False

        return super().validate(state)

    def execute(self):
        self.move_action.execute()

        self.state.funds[self.owner] -= self.cost
        self.unit_to_repair.change_health(self.repair_amount * 10)
        self.unit_to_repair.change_fuel(self.unit_to_repair.max_fuel)
        self.unit_to_repair.change_ammo(self.unit_to_repair.max_ammo)
        self.repairing_unit.available = False

    def __str__(self) -> str:
        return f"{str(self.move_action)} then repairs unit at {self.repair_target}"

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
            can_move = self.move_action.validate(state)
            if not can_move:
                self.invalid_message = self.move_action.invalid_message
                return False

        self.unloading_unit = self.move_action.unit_to_move

        if abs(self.unload_offset[0]) + abs(self.unload_offset[1]) != 1:
            self.invalid_message = "Invalid unload direction"
            return False

        unit_at_destination = state.get_unit(self.destination)
        if unit_at_destination is not None and unit_at_destination is not self.unloading_unit:
            self.invalid_message = "Destination is occupied"
            return False
        
        if not self.unloading_unit.can_unload(self.idx):
            self.invalid_message = "Nothing to unload"
            return False

        distance = abs(self.destination[0] - self.unload_position[0]) + abs(self.destination[1] - self.unload_position[1])
        
        if distance > 1:
            self.invalid_message = "Can only unload adjacent to the unit"
            return False

        if not self.unloading_unit.can_unload(self.idx):
            self.invalid_message = "Invalid unit index"
            return False

        self.unloaded_unit = self.unloading_unit.in_load[self.idx]
        terrain = state.get_terrain(self.unload_position)
        if terrain is None:
            self.invalid_message = f"{self.unload_position} is not a valid unload position"
            return False

        if terrain.get_move_cost(self.unloaded_unit.move_type) == 0:
            self.invalid_message = f"{self.unloaded_unit} cannot be placed on {terrain}"
            return False

        own_terrain = state.get_terrain(self.destination)
        if own_terrain.get_move_cost(self.unloaded_unit.move_type) == 0:
            self.invalid_message = f"{self.unloading_unit} cannot unload while on {terrain}"
            return False

        unit_at_position = state.get_unit(self.unload_position)
        if unit_at_position:
            self.invalid_message = "Already something there"
            return False

        return super().validate(state)

    def execute(self):
        super().execute()
        self.move_action.execute()

        self.unloading_unit.unload(self.idx)
        self.state.set_unit(self.unloaded_unit, self.unload_position)
        self.unloading_unit.available = False

    def __str__(self) -> str:
        return f"{str(self.move_action)} then unloads {self.idx} at {self.unload_position}"

class ActionCOP(Action):
    def __init__(self):
        super().__init__()
    
    def validate(self, state):
        current_player = state.get_current_player()
        self.co = state.get_co(current_player)
        if self.co.cop_progress() < 1:
            self.invalid_message = "Not enough power for COP"
            return False

        return super().validate(state)

    def execute(self):
        super().execute()

        self.co.apply_cop(self.state)

class ActionSCOP(Action):
    def __init__(self):
        super().__init__()
    
    def validate(self, state):
        current_player = state.get_current_player()
        self.co = state.get_co(current_player)
        if self.co.scop_progress() < 1:
            self.invalid_message = "Not enough power for SCOP"
            return False
            
        return super().validate(state)

    def execute(self):
        super().execute()

        self.co.apply_scop(self.state)

class ActionHide(Action):
    pass
        
