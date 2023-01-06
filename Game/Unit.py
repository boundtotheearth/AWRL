from Game.MoveType import MoveType
import math

class Unit:
    code = "   "
    def __init__(self, owner):
        self.owner = owner
        self.move = 0
        self.max_health = 100
        self.health = self.max_health
        self.max_ammo = 0
        self.ammo = self.max_ammo
        self.max_fuel = 0
        self.fuel = self.max_fuel
        self.daily_fuel = 0 
        self.vision = 0
        self.range = 0
        self.move_type = MoveType.FOOT
        self.cost = 0
        self.load_capacity = 0
        self.loadables = []
        self.in_load = []
        self.attack_table = {}
        self.can_capture = False
        self.can_repair = False
        self.available = True

    def initialize(self, health=None, fuel=None, ammo=None, to_load=None):
        if health is None:
            self.health = self.max_health
        else:
            if health < 0 or health > self.max_health:
                raise Exception("Provided health is invalid")
            self.health = health

        if fuel is None:
            self.fuel = self.max_fuel
        else:
            if fuel < 0 or fuel > self.max_fuel:
                raise Exception("Provided fuel invalid")
            self.fuel = fuel

        if ammo is None:
            self.ammo = self.max_ammo
        else:
            if ammo < 0 or ammo > self.max_ammo:
                raise Exception("Provided ammo is invalid")
            self.ammo = ammo

        if to_load is None:
            self.in_load = []
        else:
            if len(to_load) > self.load_capacity or any([type(unit) not in self.loadables for unit in to_load]):
                raise Exception("Provided load is invalid")
            self.in_load = to_load

    def change_fuel(self, amount):
        self.fuel = max(0, min(self.max_fuel, self.fuel + amount))

    def change_ammo(self, amount):
        self.ammo = max(0, min(self.max_ammo, self.ammo + amount))

    def change_health(self, amount):
        self.health = max(0, min(100, self.health + amount))

    def can_combine(self):
        return self.get_display_health() < 10

    def combine_with(self, unit):
        excess_health = max(0, self.get_display_health() + unit.get_display_health() - 10)
        self.change_health(unit.health)
        self.change_ammo(unit.ammo)
        self.change_fuel(unit.fuel)
        return excess_health

    def can_load(self, unit):
        return type(unit) in self.loadables and len(self.in_load) < self.load_capacity

    def load(self, unit):
        if self.can_load(unit):
            self.in_load.append(unit)

    def can_unload(self, idx):
        return len(self.in_load) > idx

    def unload(self, idx):
        return self.in_load.pop(idx) if len(self.in_load) > idx else None

    def get_display_health(self):
        return math.ceil(self.health / 10)

    def __str__(self):
        return self.code

'''
Defines a set of units that can be used in a game, and creates instances of the units for the game.
'''
class UnitLibrary:
    def __init__(self, available_units=[]):
        self.available_unit = available_units
        self._code_to_cls = {unit_class.code: unit_class for unit_class in self.available_unit}

    def create(self, unit_code, owner, health=None, fuel=None, ammo=None, to_load=None):
        if unit_code not in self._code_to_cls:
            raise Exception(f"{unit_code} is not an available unit")
        new_unit = self._code_to_cls[unit_code](owner)
        new_unit.initialize(health, fuel, ammo, to_load)
        return new_unit

class UnitInfantry(Unit):
    code = "INF"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 3
        self.max_ammo = 0
        self.max_fuel = 99
        self.daily_fuel = 0
        self.vision = 2
        self.range = [1]
        self.move_type = MoveType.FOOT
        self.cost = 1000
        self.can_capture = True
        self.attack_table = {
            UnitAntiAir: (5, 0),
            UnitAPC: (14, 0),
            UnitArtillery: (15, 0),
            UnitBattleCopter: (7, 0),
            UnitInfantry: (55, 0),
            UnitMediumTank: (1, 0),
            UnitMech: (45, 0),
            UnitMegatank: (1, 0),
            UnitMissile: (26, 0),
            UnitNeotank: (1, 0),
            UnitPiperunner: (5, 0),
            UnitRecon: (12, 0),
            UnitRocket: (25, 0),
            UnitTransportCopter: (30, 0),
            UnitTank: (5, 0)
        }

class UnitMech(Unit):
    code = "MEC"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 2
        self.max_ammo = 3
        self.max_fuel = 70
        self.daily_fuel = 0
        self.vision = 2
        self.range = [1]
        self.move_type = MoveType.BOOT
        self.cost = 3000
        self.can_capture = True
        self.attack_table = {
            UnitAntiAir: (65, 1),
            UnitAPC: (75, 1),
            UnitArtillery: (70, 1),
            UnitBattleCopter: (9, 0),
            UnitInfantry: (65, 0),
            UnitMediumTank: (15, 1),
            UnitMech: (55, 0),
            UnitMegatank: (5, 1),
            UnitMissile: (85, 1),
            UnitNeotank: (15, 1),
            UnitPiperunner: (55, 1),
            UnitRecon: (85, 1),
            UnitRocket: (85, 1),
            UnitTransportCopter: (35, 0),
            UnitTank: (55, 1)
        }

class UnitRecon(Unit):
    code = "REC"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 8
        self.max_ammo = 0
        self.max_fuel = 80
        self.daily_fuel = 0
        self.vision = 5
        self.range = [1]
        self.move_type = MoveType.TIRES
        self.cost = 4000
        self.attack_table = {
            UnitAntiAir: (4, 0),
            UnitAPC: (45, 0),
            UnitArtillery: (45, 0),
            UnitBattleCopter: (12, 0),
            UnitInfantry: (70, 0),
            UnitMediumTank: (1, 0),
            UnitMech: (65, 0),
            UnitMegatank: (1, 0),
            UnitMissile: (28, 0),
            UnitNeotank: (1, 0),
            UnitPiperunner: (6, 0),
            UnitRecon: (35, 0),
            UnitRocket: (55, 0),
            UnitTransportCopter: (35, 0),
            UnitTank: (6, 0)
        }
    

class UnitTransportCopter(Unit):
    code = "TCP"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 6
        self.max_ammo = 0
        self.max_fuel = 99
        self.daily_fuel = 2
        self.vision = 2
        self.range = [0]
        self.move_type = MoveType.AIR
        self.cost = 5000
        self.load_capacity = 1
        self.loadables = [
            UnitInfantry,
            UnitMech
        ]

class UnitAPC(Unit):
    code = "APC"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 6
        self.max_ammo = 0
        self.max_fuel = 70
        self.daily_fuel = 0
        self.vision = 1
        self.range = [0]
        self.move_type = MoveType.THREADS
        self.cost = 5000
        self.load_capacity = 1
        self.can_repair = True
        self.repair_amount = 0 # Can only resupply
        self.loadables = [
            UnitInfantry,
            UnitMech
        ]

class UnitArtillery(Unit):
    code = "ATY"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 5
        self.max_ammo = 9
        self.max_fuel = 50
        self.daily_fuel = 0
        self.vision = 1
        self.range = [2,3]
        self.move_type = MoveType.THREADS
        self.cost = 6000
        self.attack_table = {
            UnitAntiAir: (75, 1),
            UnitAPC: (70, 1),
            UnitArtillery: (75, 1),
            UnitBattleship: (40, 1),
            UnitBlackBoat: (55, 1),
            UnitCarrier: (45, 1),
            UnitCruiser: (65, 1),
            UnitInfantry: (90, 1),
            UnitLander: (55, 1),
            UnitMediumTank: (45, 1),
            UnitMech: (85, 1),
            UnitMegatank: (15, 1),
            UnitMissile: (80, 1),
            UnitNeotank: (40, 1),
            UnitPiperunner: (70, 1),
            UnitRecon: (80, 1),
            UnitRocket: (80, 1),
            UnitSubmarine: (60, 1),
            UnitTank: (70, 1)
        }

class UnitTank(Unit):
    code = "TNK"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 6
        self.max_ammo = 9
        self.max_fuel = 70
        self.daily_fuel = 0
        self.vision = 3
        self.range = [1]
        self.move_type = MoveType.THREADS
        self.cost = 7000
        self.attack_table = {
            UnitAntiAir: (65, 1),
            UnitAPC: (75, 1),
            UnitArtillery: (70, 1),
            UnitBattleCopter: (10, 0),
            UnitBattleship: (1, 1),
            UnitBlackBoat: (10, 1),
            UnitCarrier: (1, 1),
            UnitCruiser: (5, 1),
            UnitInfantry: (75, 0),
            UnitLander: (10, 1),
            UnitMediumTank: (15, 1),
            UnitMech: (70, 0),
            UnitMegatank: (10, 1),
            UnitMissile: (85, 1),
            UnitNeotank: (15, 1),
            UnitPiperunner: (55, 1),
            UnitRecon: (85, 1),
            UnitRocket: (85, 1),
            UnitSubmarine: (1, 1),
            UnitTransportCopter: (40, 0),
            UnitTank: (55, 1)
        }

class UnitBlackBoat(Unit):
    code = "BLB"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 7
        self.max_ammo = 0
        self.max_fuel = 50
        self.daily_fuel = 1
        self.vision = 1
        self.range = [0]
        self.move_type = MoveType.LANDER
        self.cost = 7500
        self.load_capacity = 2
        self.can_repair = True
        self.repair_amount = 1
        self.loadables = [
            UnitInfantry,
            UnitMech
        ]
    
class UnitAntiAir(Unit):
    code = "AAR"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 6
        self.max_ammo = 9
        self.max_fuel = 60
        self.daily_fuel = 0
        self.vision = 2
        self.range = [1]
        self.move_type = MoveType.THREADS
        self.cost = 8000
        self.attack_table = {
            UnitAntiAir: (45, 1),
            UnitAPC: (50, 1),
            UnitArtillery: (50, 1),
            UnitBattleCopter: (120, 1),
            UnitBlackBomb: (120, 1),
            UnitBomber: (75, 1),
            UnitFighter: (65, 1),
            UnitInfantry: (105, 1),
            UnitMediumTank: (10, 1),
            UnitMech: (105, 1),
            UnitMegatank: (1, 1),
            UnitMissile: (55, 1),
            UnitNeotank: (5, 1),
            UnitPiperunner: (25, 1),
            UnitRecon: (60, 1),
            UnitRocket: (55, 1),
            UnitStealth: (75, 1),
            UnitTransportCopter: (120, 1),
            UnitTank: (25, 1)
        }

class UnitBattleCopter(Unit):
    code = "BCP"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 6
        self.max_ammo = 6
        self.max_fuel = 99
        self.daily_fuel = 2
        self.vision = 3
        self.range = 1
        self.move_type = MoveType.AIR
        self.cost = 9000
        self.attack_table = {
            UnitAntiAir: (25, 1),
            UnitAPC: (60, 1),
            UnitArtillery: (65, 1),
            UnitBattleCopter: (65, 1),
            UnitBattleship: (25, 1),
            UnitBlackBoat: (25, 1),
            UnitCarrier: (25, 1),
            UnitCruiser: (55, 1),
            UnitInfantry: (75, 0),
            UnitLander: (25, 1),
            UnitMediumTank: (25, 1),
            UnitMech: (75, 0),
            UnitMegatank: (10, 1),
            UnitMissile: (65, 1),
            UnitNeotank: (20, 1),
            UnitPiperunner: (55, 1),
            UnitRecon: (55, 1),
            UnitRocket: (65, 1),
            UnitSubmarine: (25, 1),
            UnitTransportCopter: (95, 0),
            UnitTank: (55, 1)
        }

class UnitMissile(Unit):
    code = "MIS"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 4
        self.max_ammo = 6
        self.max_fuel = 50
        self.daily_fuel = 0
        self.vision = 5
        self.range = [3,4,5]
        self.move_type = MoveType.TIRES
        self.cost = 12000
        self.attack_table = {
            UnitBattleCopter: (120, 1),
            UnitBlackBomb: (120, 1),
            UnitBomber: (100, 1),
            UnitFighter: (100, 1),
            UnitStealth: (100, 1),
            UnitTransportCopter: (120, 1),
        }

class UnitRocket(Unit):
    code = "ROK"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 5
        self.max_ammo = 6
        self.max_fuel = 50
        self.daily_fuel = 0
        self.vision = 1
        self.range = [3,4,5]
        self.move_type = MoveType.TIRES
        self.cost = 15000
        self.attack_table = {
            UnitAntiAir: (85, 1),
            UnitAPC: (80, 1),
            UnitArtillery: (80, 1),
            UnitBattleship: (55, 1),
            UnitBlackBoat: (60, 1),
            UnitCarrier: (60, 1),
            UnitCruiser: (85, 1),
            UnitInfantry: (95, 1),
            UnitLander: (60, 1),
            UnitMediumTank: (55, 1),
            UnitMech: (90, 1),
            UnitMegatank: (25, 1),
            UnitMissile: (90, 1),
            UnitNeotank: (50, 1),
            UnitPiperunner: (80, 1),
            UnitRecon: (90, 1),
            UnitRocket: (85, 1),
            UnitSubmarine: (85, 1),
            UnitTank: (80, 1)
        }

class UnitMediumTank(Unit):
    code = "MTK"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 5
        self.max_ammo = 8
        self.max_fuel = 50
        self.daily_fuel = 0
        self.vision = 1
        self.range = [1]
        self.move_type = MoveType.THREADS
        self.cost = 16000
        self.attack_table = {
            UnitAntiAir: (105, 1),
            UnitAPC: (105, 1),
            UnitArtillery: (105, 1),
            UnitBattleCopter: (12, 0),
            UnitBattleship: (10, 1),
            UnitBlackBoat: (35, 1),
            UnitCarrier: (10, 1),
            UnitCruiser: (45, 1),
            UnitInfantry: (105, 0),
            UnitLander: (35, 1),
            UnitMediumTank: (55, 1),
            UnitMech: (95, 0),
            UnitMegatank: (25, 1),
            UnitMissile: (105, 1),
            UnitNeotank: (45, 1),
            UnitPiperunner: (85, 1),
            UnitRecon: (105, 1),
            UnitRocket: (105, 1),
            UnitSubmarine: (10, 1),
            UnitTransportCopter: (45, 0),
            UnitTank: (85, 1)
        }

class UnitCruiser(Unit):
    code = "CRU"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 6
        self.max_ammo = 9
        self.max_fuel = 99
        self.daily_fuel = 1
        self.vision = 3
        self.range = [1]
        self.move_type = MoveType.SEA
        self.cost = 18000
        self.load_capacity = 2
        self.loadables = [
            UnitTransportCopter,
            UnitBattleCopter
        ]
        self.attack_table = {
            UnitBattleCopter: (115, 0),
            UnitBlackBoat: (25, 1),
            UnitBlackBomb: (120, 0),
            UnitBomber: (65, 0),
            UnitCarrier: (5, 1),
            UnitFighter: (55, 0),
            UnitStealth: (100, 0),
            UnitSubmarine: (90, 1),
            UnitTransportCopter: (115, 0),
        }

class UnitFighter(Unit):
    code = "FGT"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 9
        self.max_ammo = 9
        self.max_fuel = 99
        self.daily_fuel = 5
        self.vision = 2
        self.range = [1]
        self.move_type = MoveType.AIR
        self.cost = 20000
        self.attack_table = {
            UnitBattleCopter: (100, 1),
            UnitBlackBomb: (120, 1),
            UnitBomber: (100, 1),
            UnitFighter: (55, 1),
            UnitStealth: (85, 1),
            UnitTransportCopter: (100, 1),
        }

class UnitPiperunner(Unit):
    code = "PRN"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 9
        self.max_ammo = 9
        self.max_fuel = 99
        self.daily_fuel = 0
        self.vision = 4
        self.range = [2,3,4,5]
        self.move_type = MoveType.PIPE
        self.cost = 20000
        self.attack_table = {
            UnitAntiAir: (85, 1),
            UnitAPC: (80, 1),
            UnitArtillery: (80, 1),
            UnitBattleCopter: (105, 1),
            UnitBattleship: (55, 1),
            UnitBlackBoat: (60, 1),
            UnitBlackBomb: (120, 1),
            UnitBomber: (75, 1),
            UnitCarrier: (60, 1),
            UnitCruiser: (85, 1),
            UnitFighter: (65, 1),
            UnitInfantry: (95, 1),
            UnitLander: (60, 1),
            UnitMediumTank: (55, 1),
            UnitMech: (90, 1),
            UnitMegatank: (25, 1),
            UnitMissile: (90, 1),
            UnitNeotank: (50, 1),
            UnitPiperunner: (80, 1),
            UnitRecon: (90, 1),
            UnitRocket: (85, 1),
            UnitStealth: (75, 1),
            UnitSubmarine: (85, 1),
            UnitTransportCopter: (105, 1),
            UnitTank: (80, 1)
        }

class UnitSubmarine(Unit):
    code = "SUB"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 5
        self.max_ammo = 6
        self.max_fuel = 60
        self.daily_fuel = 1
        self.vision = 5
        self.range = [1]
        self.move_type = MoveType.SEA
        self.cost = 20000
        self.attack_table = {
            UnitBattleship: (55, 1),
            UnitBlackBoat: (95, 1),
            UnitCarrier: (75, 1),
            UnitCruiser: (25, 1),
            UnitLander: (95, 1),
            UnitSubmarine: (55, 1),
        }

class UnitNeotank(Unit):
    code = "NTK"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 6
        self.max_ammo = 9
        self.max_fuel = 99
        self.daily_fuel = 0
        self.vision = 1
        self.range = [1]
        self.move_type = MoveType.THREADS
        self.cost = 22000
        self.attack_table = {
            UnitAntiAir: (115, 1),
            UnitAPC: (125, 1),
            UnitArtillery: (115, 1),
            UnitBattleCopter: (22, 0),
            UnitBattleship: (15, 1),
            UnitBlackBoat: (40, 1),
            UnitCarrier: (15, 1),
            UnitCruiser: (50, 1),
            UnitInfantry: (125, 0),
            UnitLander: (50, 1),
            UnitMediumTank: (75, 1),
            UnitMech: (115, 0),
            UnitMegatank: (35, 1),
            UnitMissile: (125, 1),
            UnitNeotank: (55, 1),
            UnitPiperunner: (105, 1),
            UnitRecon: (125, 1),
            UnitRocket: (125, 1),
            UnitSubmarine: (15, 1),
            UnitTransportCopter: (55, 0),
            UnitTank: (105, 1)
        }

class UnitBomber(Unit):
    code = "BMB"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 7
        self.max_ammo = 9
        self.max_fuel = 99
        self.daily_fuel = 5
        self.vision = 2
        self.range = [1]
        self.move_type = MoveType.AIR
        self.cost = 22000
        self.attack_table = {
            UnitAntiAir: (95, 1),
            UnitAPC: (105, 1),
            UnitArtillery: (105, 1),
            UnitBattleship: (75, 1),
            UnitBlackBoat: (95, 1),
            UnitCarrier: (75, 1),
            UnitCruiser: (85, 1),
            UnitInfantry: (110, 1),
            UnitLander: (95, 1),
            UnitMediumTank: (95, 1),
            UnitMech: (110, 1),
            UnitMegatank: (35, 1),
            UnitMissile: (105, 1),
            UnitNeotank: (90, 1),
            UnitPiperunner: (105, 1),
            UnitRecon: (105, 1),
            UnitRocket: (105, 1),
            UnitSubmarine: (95, 1),
            UnitTank: (105, 1)
        }

class UnitStealth(Unit):
    code = "STH"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 6
        self.max_ammo = 6
        self.max_fuel = 60
        self.daily_fuel = 5
        self.vision = 4
        self.range = [1]
        self.move_type = MoveType.AIR
        self.cost = 24000
        self.attack_table = {
            UnitAntiAir: (50, 1),
            UnitAPC: (85, 1),
            UnitArtillery: (75, 1),
            UnitBattleCopter: (85, 1),
            UnitBattleship: (45, 1),
            UnitBlackBoat: (65, 1),
            UnitBlackBomb: (120, 1),
            UnitBomber: (70, 1),
            UnitCarrier: (45, 1),
            UnitCruiser: (35, 1),
            UnitFighter: (45, 1),
            UnitInfantry: (90, 1),
            UnitLander: (65, 1),
            UnitMediumTank: (70, 1),
            UnitMech: (90, 1),
            UnitMegatank: (15, 1),
            UnitMissile: (85, 1),
            UnitNeotank: (60, 1),
            UnitPiperunner: (80, 1),
            UnitRecon: (85, 1),
            UnitRocket: (85, 1),
            UnitStealth: (55, 1),
            UnitSubmarine: (55, 1),
            UnitTransportCopter: (95, 1),
            UnitTank: (75, 1)
        }

class UnitBlackBomb(Unit):
    code = "BBB"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 9
        self.max_ammo = 0
        self.max_fuel = 45
        self.daily_fuel = 5
        self.vision = 1
        self.range = [0]
        self.move_type = MoveType.AIR
        self.cost = 25000
        
class UnitBattleship(Unit):
    code = "BSP"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 5
        self.max_ammo = 9
        self.max_fuel = 99
        self.daily_fuel = 1
        self.vision = 2
        self.range = [2,3,4,5,6]
        self.move_type = MoveType.SEA
        self.cost = 28000
        self.attack_table = {
            UnitAntiAir: (85, 1),
            UnitAPC: (80, 1),
            UnitArtillery: (80, 1),
            UnitBattleship: (50, 1),
            UnitBlackBoat: (95, 1),
            UnitCarrier: (60, 1),
            UnitCruiser: (95, 1),
            UnitInfantry: (95, 1),
            UnitLander: (95, 1),
            UnitMediumTank: (55, 1),
            UnitMech: (90, 1),
            UnitMegatank: (25, 1),
            UnitMissile: (90, 1),
            UnitNeotank: (50, 1),
            UnitPiperunner: (80, 1),
            UnitRecon: (90, 1),
            UnitRocket: (85, 1),
            UnitSubmarine: (95, 1),
            UnitTank: (80, 1)
        }

class UnitMegatank(Unit):
    code = "MGT"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 4
        self.max_ammo = 3
        self.max_fuel = 50
        self.daily_fuel = 0
        self.vision = 1
        self.range = [1]
        self.move_type = MoveType.THREADS
        self.cost = 28000
        self.attack_table = {
            UnitAntiAir: (195, 1),
            UnitAPC: (195, 1),
            UnitArtillery: (195, 1),
            UnitBattleCopter: (22, 0),
            UnitBattleship: (45, 1),
            UnitBlackBoat: (105, 1),
            UnitCarrier: (45, 1),
            UnitCruiser: (65, 1),
            UnitInfantry: (135, 0),
            UnitLander: (75, 1),
            UnitMediumTank: (125, 1),
            UnitMech: (125, 0),
            UnitMegatank: (65, 1),
            UnitMissile: (195, 1),
            UnitNeotank: (115, 1),
            UnitPiperunner: (180, 1),
            UnitRecon: (195, 1),
            UnitRocket: (195, 1),
            UnitSubmarine: (45, 1),
            UnitTransportCopter: (55, 0),
            UnitTank: (180, 1)
        }

class UnitCarrier(Unit):
    code = "CAR"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 5
        self.max_ammo = 9
        self.max_fuel = 99
        self.daily_fuel = 1
        self.vision = 4
        self.range = [3,4,5,6,7,8]
        self.move_type = MoveType.SEA
        self.cost = 30000
        self.load_capacity = 2
        self.loadables = [
            UnitTransportCopter,
            UnitBattleCopter,
            UnitFighter,
            UnitBomber,
            UnitBlackBomb,
            UnitStealth
        ]
        self.attack_table = {
            UnitBattleCopter: (115, 1),
            UnitBlackBomb: (120, 1),
            UnitBomber: (100, 1),
            UnitFighter: (100, 1),
            UnitStealth: (100, 1),
            UnitTransportCopter: (115, 1)
        }

class UnitLander(Unit):
    code = "LND"
    def __init__(self, owner):
        super().__init__(owner)
        self.move = 6
        self.max_ammo = 0
        self.max_fuel = 99
        self.daily_fuel = 1
        self.vision = 1
        self.range = [0]
        self.move_type = MoveType.LANDER
        self.cost = 12000
        self.load_capacity = 2
        self.loadables = [
            UnitInfantry,
            UnitMech,
            UnitAntiAir,
            UnitMissile,
            UnitAPC,
            UnitArtillery,
            UnitRocket,
            UnitAPC,
            UnitRecon,
            UnitTank,
            UnitMediumTank,
            UnitNeotank,
            UnitMegatank,
        ]

standard_units = [
    UnitInfantry,
    UnitMech,
    UnitRecon,
    UnitTransportCopter,
    UnitAPC,
    UnitArtillery,
    UnitTank,
    UnitBlackBoat,
    UnitAntiAir,
    UnitBattleCopter,
    UnitMissile,
    UnitLander,
    UnitRocket,
    UnitMediumTank,
    UnitCruiser,
    UnitFighter,
    UnitPiperunner,
    UnitSubmarine,
    UnitNeotank,
    UnitBomber,
    UnitStealth,
    UnitBlackBomb,
    UnitBattleship,
    UnitMegatank,
    UnitCarrier,
]