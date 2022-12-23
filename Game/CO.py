import random
from Game.Unit import UnitInfantry, UnitMech, UnitRecon, UnitTransportCopter, UnitAPC, UnitArtillery, UnitTank, UnitBlackBoat, UnitAntiAir, UnitBattleCopter, UnitMissile, UnitLander, UnitRocket, UnitMediumTank, UnitCruiser, UnitFighter, UnitPiperunner, UnitSubmarine, UnitNeotank, UnitBomber, UnitStealth, UnitBlackBomb, UnitBattleship, UnitMegatank, UnitCarrier

class COLibrary:
    def __init__(self, available_co):
        self.available_co = available_co
        self._code_to_cls = {co_class.name: co_class for co_class in self.available_co}

    def create(self, co_name):
        if co_name not in self._code_to_cls:
            raise Exception("{co_name} is not an available CO".format(co_name=co_name))
        
        co_type = self._code_to_cls[co_name]
        return co_type()
    
    def is_valid(self, co_id=None, co_cls=None, co_name=None):
        return (co_id is not None and co_id >= 0 and co_id < len(self.available_co)) or \
            (co_cls is not None and co_cls in self.available_co) or \
            (co_name is not None and co_name in self._code_to_cls)

    
class BaseCO:
    name = "None"
    def __init__(self):
        self.modifiers = {
            UnitAntiAir: (100, 100),
            UnitAPC: (100, 100),
            UnitArtillery: (100, 100),
            UnitBattleCopter: (100, 100),
            UnitBattleship: (100, 100),
            UnitBlackBoat: (100, 100),
            UnitBlackBomb: (100, 100),
            UnitBomber: (100, 100),
            UnitCarrier: (100, 100),
            UnitCruiser: (100, 100),
            UnitFighter: (100, 100),
            UnitInfantry: (100, 100),
            UnitLander: (100, 100),
            UnitMediumTank: (100, 100),
            UnitMech: (100, 100),
            UnitMegatank: (100, 100),
            UnitMissile: (100, 100),
            UnitNeotank: (100, 100),
            UnitPiperunner: (100, 100),
            UnitRecon: (100, 100),
            UnitRocket: (100, 100),
            UnitStealth: (100, 100),
            UnitSubmarine: (100, 100),
            UnitTransportCopter: (100, 100),
            UnitTank: (100, 100)
        }

    def get_attack_modifier(self, unit_type):
        return self.modifiers.get(unit_type, (0, 0))[0]
    
    def get_defence_modifier(self, unit_type):
        return self.modifiers.get(unit_type, (0, 0))[1]

    def get_luck_roll(self):
        return random.randint(0, 9)

all_co = [
    BaseCO
]