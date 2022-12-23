from Game.Action import ActionEnd
from ActionParser import ActionParser

import numpy as np
import random

class Agent:
    def get_action(self, observation, action_masks):
        raise Exception("Not Implemented")

class DoNothingAgent(Agent):
    def get_action(self, observation, action_masks):
        return ActionEnd()

class RandomAgent(Agent):
    def get_action(self, observation, action_masks):
        action = np.random.choice(np.where(action_masks)[0])
        return action
        
class AIAgent(Agent):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def get_action(self, observation, action_masks):
        action, _state = self.model.predict(observation, action_masks=action_masks)
        return action.tolist()

class HumanAgent(Agent):
    def __init__(self):
        super().__init__()
        self.parser = ActionParser()

    def get_action(self, observation, action_masks):
        while True:
            player_input = input("Your Move:")
            action = self.parser.parse(player_input)
            if action is not None:
                return action
            else:
                print("Invalid Action")

class FileAgent(Agent):
    def __init__(self, file):
        super().__init__()
        self.parser = ActionParser()
        with open(file) as input_file:
            self.input_lines = iter(input_file.readlines())
    
    def get_action(self, observation, action_masks):
        return self.parser.parser(next(self.input_lines))