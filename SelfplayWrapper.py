from gym import Wrapper

class SelfplayWrapper(Wrapper):
    def __init__(self, env, agent_player, opponents) -> None:
        super().__init__(env)
        self.agent_player = agent_player
        self.opponents = opponents

    def reset(self):
        observation = super().reset()
        observation, reward, done, info = self.play_opponent_turns(observation)
        
        return observation

    def step(self, action):
        observation, reward, done, info = self.env.step(action)

        if done:
            return observation, reward, done, info

        observation, reward, done, info = self.play_opponent_turns(observation)

        reward = 0
        winner = self.game.state.check_winner()
        if winner is self.agent_player:
            reward = 1
        elif winner is not None:
            reward = -1
        else:
            reward = -0.001
        
        return observation, reward, done, info

    def play_opponent_turns(self, init_observation):
        observation = init_observation
        reward = 0
        done = False
        info = {}

        while(self.game.state.get_current_player() is not self.agent_player):
            opponent_player = self.game.state.get_current_player()
            opponent_agent = self.opponents[opponent_player]
            opponent_action = opponent_agent.get_action(observation, self.action_masks())
            observation, reward, done, info = self.env.step(opponent_action)
            if done:
                break

        return observation, reward, done, info

            
