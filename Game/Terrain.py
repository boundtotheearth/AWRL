from Game.MoveType import MoveType
from Game.Unit import UnitInfantry, UnitMech, UnitRecon, UnitTransportCopter, UnitAPC, UnitArtillery, UnitTank, UnitBlackBoat, UnitAntiAir, UnitBattleCopter, UnitMissile, UnitLander, UnitRocket, UnitMediumTank, UnitCruiser, UnitFighter, UnitPiperunner, UnitSubmarine, UnitNeotank, UnitBomber, UnitStealth, UnitBlackBomb, UnitBattleship, UnitMegatank, UnitCarrier
import math

class Terrain(object):
    code = "   "
    defense = 1
    costs = {}

    def get_move_cost(self, move_type):
        return self.costs.get(move_type, 0)

    def __str__(self):
        return self.code

class Property(Terrain):
    income=1000
    costs={
        MoveType.FOOT:1,
        MoveType.BOOT:1,
        MoveType.THREADS:1,
        MoveType.TIRES:1,
        MoveType.SEA:0,
        MoveType.LANDER:0,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
    buildables = []

    def __init__(self, owner, capture_amount=20):
        super().__init__()

        self.owner = owner
        self.capture_amount = capture_amount

    def change_capture(self, new_owner, amount):
        self.capture_amount = min(20, math.floor(self.capture_amount + amount))
        if self.capture_amount <= 0:
            self.capture_amount = 20
            self.owner = new_owner

    def __str__(self):
        return self.code.replace(".", self.owner)

'''
Defines a set of terrain that can be used in a game, and creates instances of the terrain for the game.
A new subclass should be created for terrain sets catering to specific game formats and requirements
'''
class TerrainLibrary:
    def __init__(self, players, available_terrain):
        self.available_terrain = available_terrain
        players = players.copy()
        players.append('N')
        self._code_to_cls = {terrain_class.code.replace('.', player): terrain_class for terrain_class in self.available_terrain for player in players}

    def create(self, terrain_code):
        if terrain_code not in self._code_to_cls:
            raise Exception("{terrain_code} is not an available terrain".format(terrain_code=terrain_code))
        
        terrain_type = self._code_to_cls[terrain_code]
        if issubclass(terrain_type, Property):
            return terrain_type(owner=terrain_code[0])
        else:
            return terrain_type()

class TerrainPlain(Terrain):
    code="PLN"
    defense=1
    costs={
        MoveType.FOOT:1,
        MoveType.BOOT:1,
        MoveType.THREADS:1,
        MoveType.TIRES:2,
        MoveType.SEA:0,
        MoveType.LANDER:0,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
class TerrainMountains(Terrain):
    code="MTN"
    defense=4
    costs={
        MoveType.FOOT:2,
        MoveType.BOOT:1,
        MoveType.THREADS:0,
        MoveType.TIRES:0,
        MoveType.SEA:0,
        MoveType.LANDER:0,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
class TerrainWoods(Terrain):
    code="WOD"
    defense=2
    costs={
        MoveType.FOOT:1,
        MoveType.BOOT:1,
        MoveType.THREADS:2,
        MoveType.TIRES:3,
        MoveType.SEA:0,
        MoveType.LANDER:0,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
class TerrainRivers(Terrain):
    code="RVR"
    defense=0
    costs={
        MoveType.FOOT:2,
        MoveType.BOOT:1,
        MoveType.THREADS:0,
        MoveType.TIRES:0,
        MoveType.SEA:0,
        MoveType.LANDER:0,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
class TerrainRoad(Terrain):
    code="ROD"
    defense=0
    costs={
        MoveType.FOOT:1,
        MoveType.BOOT:1,
        MoveType.THREADS:1,
        MoveType.TIRES:1,
        MoveType.SEA:0,
        MoveType.LANDER:0,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
class TerrainSea(Terrain):
    code="SEA"
    defense=0
    costs={
        MoveType.FOOT:0,
        MoveType.BOOT:0,
        MoveType.THREADS:0,
        MoveType.TIRES:0,
        MoveType.SEA:1,
        MoveType.LANDER:1,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
class TerrainShoals(Terrain):
    code="SHL"
    defense=0
    costs={
        MoveType.FOOT:1,
        MoveType.BOOT:1,
        MoveType.THREADS:1,
        MoveType.TIRES:1,
        MoveType.SEA:0,
        MoveType.LANDER:1,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
class TerrainReefs(Terrain):
    code="REF"
    defense=1
    costs={
        MoveType.FOOT:0,
        MoveType.BOOT:0,
        MoveType.THREADS:0,
        MoveType.TIRES:0,
        MoveType.SEA:2,
        MoveType.LANDER:2,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
class TerrainPipes(Terrain):
    code="PIP"
    defense=0
    costs={
        MoveType.FOOT:0,
        MoveType.BOOT:0,
        MoveType.THREADS:0,
        MoveType.TIRES:0,
        MoveType.SEA:0,
        MoveType.LANDER:0,
        MoveType.AIR:0,
        MoveType.PIPE:1
    }

class TerrainMissileSilo(Terrain):
    code="SIL"
    defense=3
    costs={
        MoveType.FOOT:1,
        MoveType.BOOT:1,
        MoveType.THREADS:1,
        MoveType.TIRES:1,
        MoveType.SEA:0,
        MoveType.LANDER:0,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
        
class TerrainCity(Property):
    code=".CT"
    defense=3

class TerrainHeadquarters(Property):
    code=".HQ"
    defense=4

class TerrainBase(Property):
    code=".BS"
    buildables = {
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
        UnitPiperunner
    }
class TerrainAirport(Property):
    code=".AP"
    buildables = {
        UnitTransportCopter,
        UnitBattleCopter,
        UnitFighter,
        UnitBomber,
        UnitBlackBomb,
        UnitStealth
    }
class TerrainPort(Property):
    code=".PO"
    costs={
        MoveType.FOOT:1,
        MoveType.BOOT:1,
        MoveType.THREADS:1,
        MoveType.TIRES:1,
        MoveType.SEA:1,
        MoveType.LANDER:1,
        MoveType.AIR:1,
        MoveType.PIPE:0
    }
    buildables = {
        UnitLander,
        UnitBlackBoat,
        UnitCruiser,
        UnitBattleship,
        UnitCarrier,
    }
class TerrainLab(Property):
    code=".LB"
    income=0
class TerrainCommTower(Property):
    code=".CM"

standard_terrain = [
    TerrainPlain,
    TerrainMountains,
    TerrainWoods,
    TerrainRivers,
    TerrainRoad,
    TerrainSea,
    TerrainShoals,
    TerrainReefs,
    TerrainPipes,
    TerrainMissileSilo,
    TerrainCity,
    TerrainHeadquarters,
    TerrainBase,
    TerrainAirport,
    TerrainPort,
    TerrainLab,
    TerrainCommTower
]