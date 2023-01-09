from AWEnv_Gym import AWEnv_Gym
from Agent import RandomAgent
from sb3_contrib.common.maskable.utils import get_action_masks
import time
import gc
import numpy as np

if __name__ == "__main__":
    print("Seting Up Benchmark Test...")

    num_trials = 10
    trial_times = []

    env_config = {
        "map": "Maps/Mind_Trap.json",
        "max_episode_steps": 10000,
        "render_mode": None,
        "seed": 0,
        'agent_player': 'random',
        'opponent_list': [RandomAgent()]
    }
    env = AWEnv_Gym.selfplay_env(env_config)
    
    test_agent = RandomAgent()

    gc.disable() # disable garbage collector

    print("Setup complete. Starting Test...")
    overall_timer_start_ns = time.perf_counter_ns()

    for trial_count in range(num_trials):        
        observation = env.reset()

        timestep_counter = 0
        trial_timer_start_ns = time.perf_counter_ns()
        for _ in range(200):
            action_mask = get_action_masks(env)
            action = test_agent.get_action(observation, action_mask)

            observation, reward, done, info = env.step(action)

            timestep_counter += 1

            if done:
                break
        trial_timer_end_ns = time.perf_counter_ns()
        trial_ns = trial_timer_end_ns - trial_timer_start_ns

        print(f"Trial {trial_count}: {timestep_counter} timesteps, {trial_ns}ns, {trial_ns * 1e-9}s")
        
        trial_times.append(trial_ns)
    
    overall_timer_end_ns = time.perf_counter_ns()

    gc.enable()

    total_ns = overall_timer_end_ns - overall_timer_start_ns
    print(f"Overall Execution time: {total_ns}ns, {total_ns * 1e-9}s")

    mean_ns = np.mean(trial_times)
    print(f"Mean Execution Time: {mean_ns}ns, {mean_ns * 1e-9}s")

    std_ns = np.std(trial_times)
    print(f"std: {std_ns}ns, {std_ns * 1e-9}s")
    
    