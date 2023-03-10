from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback
from stable_baselines3.common.callbacks import EventCallback
from stable_baselines3.common.vec_env import sync_envs_normalization
from sb3_contrib.common.maskable.evaluation import evaluate_policy
import os
import numpy as np
from sb3_contrib import MaskablePPO
from Agent import HumanAgent, DoNothingAgent, AIAgent, RandomAgent
from datetime import datetime
from copy import deepcopy
from stable_baselines3.common.env_util import make_vec_env
from AWEnv_Gym import AWEnv_Gym

class SelfplayCallback(EventCallback):
    def __init__(self,
        eval_freq = 10000,
        log_path = None,
        best_model_save_path = None,
        deterministic = True,
        callback_after_eval = None,
        verbose = 1,
        reward_threshold = 0.9,
        selfplay_opponents = [],
        eval_env_config = {},
        n_eval_envs = 1,
        n_eval_episodes_per_opponent = 10,
        monitor_dir=None,
        warn = True,
        render = False,
        use_masking = True,
        callback_on_new_best = None
    ):
        super().__init__(callback_after_eval, verbose=verbose)

        self.warn = warn
        self.render = render
        self.use_masking = use_masking
        self.callback_on_new_best = callback_on_new_best
        self.monitor_dir = monitor_dir

        self.eval_freq = eval_freq
        self.best_mean_reward = -np.inf
        self.last_mean_reward = -np.inf
        self.deterministic = deterministic

        self.best_model_save_path = best_model_save_path
        # Logs will be written in ``evaluations.npz``
        if log_path is not None:
            log_path = os.path.join(log_path, "evaluations")
        self.log_path = log_path
        self.evaluations_results = []
        self.evaluations_timesteps = []
        self.evaluations_length = []
        # For computing success rate
        self._is_success_buffer = []
        self.evaluations_successes = []

        self.reward_threshold = reward_threshold
        self.selfplay_opponents = selfplay_opponents
        self.eval_env_config = eval_env_config
        self.n_eval_envs = n_eval_envs
        self.n_eval_episodes_per_opponent = n_eval_episodes_per_opponent
        assert self.best_model_save_path is not None, "Need a path to save opponents to"

    def _init_callback(self) -> None:
        # Create folders if needed
        if self.best_model_save_path is not None:
            os.makedirs(self.best_model_save_path, exist_ok=True)
        if self.log_path is not None:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def _log_success_callback(self, locals_, globals_):
        """
        Callback passed to the  ``evaluate_policy`` function
        in order to log the success rate (when applicable),
        for instance when using HER.

        :param locals_:
        :param globals_:
        """
        info = locals_["info"]

        if locals_["done"]:
            maybe_is_success = info.get("is_success")
            if maybe_is_success is not None:
                self._is_success_buffer.append(maybe_is_success)

    def _on_rollout_start(self) -> None:
        print("Rollout started at", datetime.now().strftime("%H:%M:%S"))

    def _on_rollout_end(self) -> None:
        print("Rollout ended at", datetime.now().strftime("%H:%M:%S"))

    def _on_step(self) -> bool:

        continue_training = True

        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            print("Evaluation started at", datetime.now().strftime("%H:%M:%S"))
            # Sync training and eval env if there is VecNormalize
            if self.model.get_vec_normalize_env() is not None:
                try:
                    sync_envs_normalization(self.training_env, self.eval_env)
                except AttributeError as e:
                    raise AssertionError(
                        "Training and eval env are not wrapped the same way, "
                        "see https://stable-baselines3.readthedocs.io/en/master/guide/callbacks.html#evalcallback "
                        "and warning above."
                    ) from e

            # Reset success rate buffer
            self._is_success_buffer = []

            self.logger.record("league/league_size", len(self.selfplay_opponents))

            episode_rewards = []
            episode_lengths = []
            skip_eval = False
            for opponent in self.selfplay_opponents:
                if skip_eval:
                    self.logger.record(f"league/{opponent}", "Skipped")

                print(f"Evaluation against {opponent} started at", datetime.now().strftime("%H:%M:%S"))
                env_config = deepcopy(self.eval_env_config)
                env_config['opponent_list'] = [opponent]
                eval_env = make_vec_env(
                    env_id=AWEnv_Gym.selfplay_env,
                    n_envs=self.n_eval_envs,
                    env_kwargs={'env_config': env_config},
                    monitor_dir=self.monitor_dir
                )
                
                episode_rewards_for_opponent, episode_lengths_for_opponent = evaluate_policy(
                    self.model,
                    eval_env,
                    n_eval_episodes=self.n_eval_episodes_per_opponent,
                    render=self.render,
                    deterministic=self.deterministic,
                    return_episode_rewards=True,
                    warn=self.warn,
                    callback=self._log_success_callback,
                    use_masking=self.use_masking,
                )
                mean_reward_for_opponent, std_reward_for_opponent = np.mean(episode_rewards_for_opponent), np.std(episode_rewards_for_opponent)
                mean_ep_length_for_opponent, std_ep_length_for_opponent = np.mean(episode_lengths_for_opponent), np.std(episode_lengths_for_opponent)
                
                self.logger.record(f"league/{opponent}/ep_reward", f"{mean_reward_for_opponent} +/- {std_reward_for_opponent}")
                self.logger.record(f"league/{opponent}/ep_length", f"{mean_ep_length_for_opponent} +/- {std_ep_length_for_opponent}")

                episode_rewards.extend(episode_rewards_for_opponent)
                episode_lengths.extend(episode_lengths_for_opponent)

                if mean_reward_for_opponent < self.reward_threshold / 2:
                    print("Model is doing very poorly. Skipping evaluation to continue training...")
                    skip_eval = True

            if self.log_path is not None:
                self.evaluations_timesteps.append(self.num_timesteps)
                self.evaluations_results.append(episode_rewards)
                self.evaluations_length.append(episode_lengths)

                kwargs = {}
                # Save success log if present
                if len(self._is_success_buffer) > 0:
                    self.evaluations_successes.append(self._is_success_buffer)
                    kwargs = dict(successes=self.evaluations_successes)

                np.savez(
                    self.log_path,
                    timesteps=self.evaluations_timesteps,
                    results=self.evaluations_results,
                    ep_lengths=self.evaluations_length,
                    **kwargs,
                )

            mean_reward, std_reward = np.mean(episode_rewards), np.std(episode_rewards)
            mean_ep_length, std_ep_length = np.mean(episode_lengths), np.std(episode_lengths)
            self.last_mean_reward = mean_reward

            if self.verbose > 0:
                print(f"Eval num_timesteps={self.num_timesteps}, " f"episode_reward={mean_reward:.2f} +/- {std_reward:.2f}")
                print(f"Episode length: {mean_ep_length:.2f} +/- {std_ep_length:.2f}")
            # Add to current Logger
            self.logger.record("eval/mean_reward", float(mean_reward))
            self.logger.record("eval/mean_ep_length", mean_ep_length)

            if len(self._is_success_buffer) > 0:
                success_rate = np.mean(self._is_success_buffer)
                if self.verbose > 0:
                    print(f"Success rate: {100 * success_rate:.2f}%")
                self.logger.record("eval/success_rate", success_rate)

            # Dump log so the evaluation results are printed with the correct timestep
            self.logger.record("time/total_timesteps", self.num_timesteps, exclude="tensorboard")

            if mean_reward > self.best_mean_reward:
                if self.verbose > 0:
                    print("New best mean reward!")
                if self.best_model_save_path is not None:
                    self.model.save(os.path.join(self.best_model_save_path, "best_model"))
                self.best_mean_reward = mean_reward
                # Trigger callback on new best model, if needed
                if self.callback_on_new_best is not None:
                    continue_training = self.callback_on_new_best.on_step()
            
            if mean_reward > self.reward_threshold:
                if self.verbose > 0:
                    print("Exceeded reward threshold! Adding a new opponent!")
                new_model_id = len(self.selfplay_opponents)
                new_model_name = f"model_{new_model_id}"
                self.model.save(os.path.join(self.best_model_save_path, new_model_name))
                new_model = MaskablePPO.load(os.path.join(self.best_model_save_path, f"model_{new_model_id}"))
                self.selfplay_opponents.append(AIAgent(new_model, name=new_model_name, deterministic=True))
                self.best_mean_reward = -np.inf
                
            self.logger.dump(self.num_timesteps)
            print("Evaluation completed at", datetime.now().strftime("%H:%M:%S"))
                
            # Trigger callback after every evaluation, if needed
            if self.callback is not None:
                continue_training = continue_training and self._on_event()

        return continue_training

    def update_child_locals(self, locals_):
        """
        Update the references to the local variables.

        :param locals_: the local variables during rollout collection
        """
        if self.callback:
            self.callback.update_locals(locals_)