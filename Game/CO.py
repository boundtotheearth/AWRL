import random
from copy import deepcopy
from Game.Unit import standard_units

class COLibrary:
    def __init__(self, available_co):
        self.available_co = available_co
        self._code_to_cls = {co_class.name: co_class for co_class in self.available_co}

    def create(self, co_name):
        if co_name not in self._code_to_cls:
            raise Exception(f"{co_name} is not an available CO")
        
        co_type = self._code_to_cls[co_name]
        return co_type()
    
    def is_valid(self, co_id=None, co_cls=None, co_name=None):
        return (co_id is not None and co_id >= 0 and co_id < len(self.available_co)) or \
            (co_cls is not None and co_cls in self.available_co) or \
            (co_name is not None and co_name in self._code_to_cls)

    
class BaseCO:
    name = "None"
    def __init__(self):
        # Overwrite these for each CO
        self.cop_amount = 0
        self.scop_amount = 0
        self.modifiers = { unit: (100, 100) for unit in standard_units }

        self.player = None
        self.cop_applied = False
        self.scop_applied = False
        self.power = 0
        self.powers_used = 0
        self.original_modifiers = deepcopy(self.modifiers)

    def set_player(self, player):
        self.player = player

    def get_attack_modifier(self, unit_type):
        return self.modifiers.get(unit_type, (0, 0))[0]
    
    def get_defence_modifier(self, unit_type):
        return self.modifiers.get(unit_type, (0, 0))[1]

    def get_luck_roll(self):
        return random.randint(0, 9)

    def charge_power(self, amount):
        if self.cop_applied or self.scop_applied:
            return
        self.power = max(0, min(self.scop_amount, self.power + amount))

    def apply_cop(self, state):
        for unit in self.modifiers:
            original_modifier = self.modifiers[unit]
            new_modifier = (original_modifier[0] + 10, original_modifier[1] + 10)
            self.modifiers[unit] = new_modifier

        self.cop_applied = True
        self.powers_used = min(10, self.powers_used + 1)
        self.power = 0

    def apply_scop(self, state):
        for unit in self.modifiers:
            original_modifier = self.modifiers[unit]
            new_modifier = (original_modifier[0] + 10, original_modifier[1] + 10)
            self.modifiers[unit] = new_modifier
        
        self.scop_applied = True
        self.powers_used = min(10, self.powers_used + 1)
        self.power = 0

    def reset_cop(self, state):
        self.modifiers = deepcopy(self.original_modifiers)
        self.cop_applied = False

    def reset_scop(self, state):
        self.modifiers = deepcopy(self.original_modifiers)
        self.scop_applied = False

class COAdder(BaseCO):
    name = "Adder"

    def __init__(self):
        super().__init__()
        self.cop_amount = 2 * 9000
        self.scop_amount = 5 * 9000

    def apply_cop(self, state):
        for unit in state.get_all_units(owner=self.player).values():
            unit.move += 1

        # Update movement costs due to new move range
        state.update_movement_cost()
        
        super().apply_cop(state)

    def apply_scop(self, state):
        for unit in state.get_all_units(owner=self.player).values():
            unit.move += 2

        # Update movement costs due to new move range
        state.update_movement_cost()

        super().apply_scop(state)

    def reset_cop(self, state):
        for unit in state.get_all_units(owner=self.player).values():
            unit.move -= 1

        super().reset_cop(state)

    def reset_scop(self, state):
        for unit in state.get_all_units(owner=self.player).values():
            unit.move -= 2

        super().reset_scop(state)

all_co = [
    BaseCO,
    COAdder
]