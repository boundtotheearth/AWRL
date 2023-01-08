from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback
from stable_baselines3.common.vec_env import sync_envs_normalization
from sb3_contrib.common.maskable.evaluation import evaluate_policy
import os
import numpy as np
from sb3_contrib import MaskablePPO
from Agent import HumanAgent, DoNothingAgent, AIAgent, RandomAgent
from datetime import datetime

class SelfplayCallback(MaskableEvalCallback):
    def __init__(self, *args, reward_threshold = 0.9, selfplay_opponents = [], **kwargs):
        super().__init__(*args, **kwargs)
        self.reward_threshold = reward_threshold
        self.selfplay_opponents = selfplay_opponents
        assert self.best_model_save_path is not None, "Need a path to save opponents to"

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

            # Note that evaluate_policy() has been patched to support masking
            episode_rewards, episode_lengths = evaluate_policy(
                self.model,
                self.eval_env,
                n_eval_episodes=self.n_eval_episodes,
                render=self.render,
                deterministic=self.deterministic,
                return_episode_rewards=True,
                warn=self.warn,
                callback=self._log_success_callback,
                use_masking=self.use_masking,
            )

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
                self.model.save(os.path.join(self.best_model_save_path, f"model_{new_model_id}"))
                new_model = MaskablePPO.load(os.path.join(self.best_model_save_path, f"model_{new_model_id}"))
                self.selfplay_opponents.append(AIAgent(new_model))
                self.best_mean_reward = -np.inf
                
            self.logger.record("eval/league_size", len(self.selfplay_opponents))
            self.logger.dump(self.num_timesteps)
            print("Evaluation completed at", datetime.now().strftime("%H:%M:%S"))
                
            # Trigger callback after every evaluation, if needed
            if self.callback is not None:
                continue_training = continue_training and self._on_event()

        return continue_training