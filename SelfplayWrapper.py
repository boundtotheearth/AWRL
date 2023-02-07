from gym import Wrapper
import random

class SelfplayWrapper(Wrapper):
    def __init__(self, env, agent_player, opponent_list) -> None:
        super().__init__(env)
        self.opponent_list = opponent_list
        self.agent_player = random.choice(self.env.game.players) if agent_player == 'random' else agent_player
        if agent_player == 'random':
            self.agent_player = random.choice(self.env.game.players)
        elif agent_player == 'alternate':
            self.agent_player == 'O'
        else:
            self.agent_player == 'O'

        assert self.agent_player in self.env.game.players
        
        self._reset_opponents()

    def reset(self):
        observation = super().reset()

        if self.env_config['agent_player'] == 'random':
            self.agent_player = random.choice(self.env.game.players)
        elif self.env_config['agent_player'] == 'alternate':
            self.agent_player == 'O' if self.agent_player == 'B' else 'O'

        self._reset_opponents()

        observation, reward, done, info = self.play_opponent_turns(observation)
        
        return observation

    def _reset_opponents(self):
        self.opponents = {}
        for player in self.env.game.players:
            if player is not self.agent_player:
                self.opponents[player] = random.choices(self.opponent_list, weights=[2**i for i in range(len(self.opponent_list))])[0]

    def step(self, action):
        observation, reward, done, info = self.env.step(action)

        if self.game.get_current_player() is not self.agent_player and not done:
            observation, _, done, info = self.play_opponent_turns(observation)
            winner = self.env.game.state.check_winner()
            reward = self.env.calculate_reward(self.agent_player, winner)
        
        return observation, reward, done, info

    def play_opponent_turns(self, init_observation):
        observation = init_observation
        reward = 0
        done = False
        info = {}

        while self.game.get_current_player() is not self.agent_player:
            opponent_player = self.game.get_current_player()
            opponent_agent = self.opponents[opponent_player]
            opponent_action = opponent_agent.get_action(observation, self.action_masks())
            observation, reward, done, info = self.env.step(opponent_action)
            if done:
                break

        return observation, reward, done, info

            
