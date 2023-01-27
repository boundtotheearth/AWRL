import gym
import torch as th
from torch import nn
import math

from stable_baselines3.common.torch_layers import BaseFeaturesExtractor, FlattenExtractor
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.preprocessing import get_action_dim

class SqueezeExcitation(nn.Module):
    """
    This block implements the Squeeze-and-Excitation block from https://arxiv.org/abs/1709.01507 (see Fig. 1).
    Parameters ``activation``, and ``scale_activation`` correspond to ``delta`` and ``sigma`` in eq. 3.

    Args:
        input_channels (int): Number of channels in the input image
        squeeze_channels (int): Number of squeeze channels
        activation (Callable[..., torch.nn.Module], optional): ``delta`` activation. Default: ``torch.nn.ReLU``
        scale_activation (Callable[..., torch.nn.Module]): ``sigma`` activation. Default: ``torch.nn.Sigmoid``
    """

    def __init__(
        self,
        input_channels,
        squeeze_channels,
        activation = nn.ReLU,
        scale_activation = nn.Sigmoid,
    ) -> None:
        super().__init__()
        self.avgpool = nn.AdaptiveAvgPool2d(1)
        self.fc1 = nn.Conv2d(input_channels, squeeze_channels, 1)
        self.fc2 = nn.Conv2d(squeeze_channels, input_channels, 1)
        self.activation = activation()
        self.scale_activation = scale_activation()

    def _scale(self, input):
        scale = self.avgpool(input)
        scale = self.fc1(scale)
        scale = self.activation(scale)
        scale = self.fc2(scale)
        return self.scale_activation(scale)

    def forward(self, input):
        scale = self._scale(input)
        return scale * input

class ResBlock(nn.Module):
    def __init__(self):
        super().__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(128, 128, kernel_size=5, padding='same'),
            nn.LeakyReLU(),
            nn.Conv2d(128, 128, kernel_size=5, padding='same'),
            SqueezeExcitation(128, 128)
        )
        self.leakyRelu = nn.LeakyReLU()
    
    def forward(self, obs):
        residual = obs
        result = self.conv(obs)
        result += residual
        result = self.leakyRelu(result)
        return result

class InputEncoder(nn.Module):
    def __init__(self, input_channels) -> None:
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(input_channels, 128, kernel_size=1),
            nn.LeakyReLU()
        )
    
    def forward(self, input):
        return self.encoder(input)

class CustomConvLayer(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        
        self.model = nn.Sequential(
            nn.Conv2d(input_dim, 128, kernel_size=3, padding='same'),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, padding='same'),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, padding='same'),
            nn.ReLU(),
            nn.Flatten()
        )

    def forward(self, obs):
        reshaped_obs = obs.view(obs.shape[0], -1, obs.shape[-2], obs.shape[-1])
        return self.model(reshaped_obs)


class CustomFeatureExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space):
        super().__init__(observation_space, features_dim=1)

        self.map_dims = observation_space['terrain'].shape[-2:]

        input_channels = 0
        for key, space in observation_space.spaces.items():
            if len(space.shape) >= 3:
                input_channels += math.prod(space.shape[:-2])
            elif len(space.shape) < 2:
                input_channels += math.prod(space.shape)
        
        self.input_encoder = InputEncoder(input_channels=input_channels)
        self.resnet = nn.Sequential(
            ResBlock(),
            ResBlock(),
            ResBlock(),
            ResBlock(),
            ResBlock(),
            ResBlock(),
            ResBlock(),
            ResBlock()
        )

        features_dim = 128 * math.prod(self.map_dims)

        self._features_dim = features_dim
        
    def forward(self, observations):
        #Concatenate all layers, broadcasting if neccessary
        combined_obs = []
        for key, obs in observations.items():
            if obs.ndim-1 >= 3:
                combined_obs.append(obs.flatten(start_dim=1, end_dim=-3))
            elif obs.ndim-1 < 2:
                combined_obs.append(obs.unsqueeze(-1).unsqueeze(-1).repeat([1, 1, self.map_dims[0], self.map_dims[1]]))

        combined_obs = th.cat(combined_obs, dim=1)

        encoded_input = self.input_encoder(combined_obs)
        features = self.resnet(encoded_input)
        features = features.flatten(start_dim=1)

        return features

class CustomActorCriticPolicy(ActorCriticPolicy):
    #need to define custom action network (self.action_net) to handle action embeddings via dot product instead of an mlp
    def __init__(self, 
        observation_space, 
        action_space, 
        lr_schedule, 
        net_arch = None, 
        activation_fn = nn.Tanh, 
        ortho_init = True, 
        use_sde = False, 
        log_std_init = 0, 
        full_std = True, 
        sde_net_arch = None, 
        use_expln = False, 
        squash_output = False, 
        features_extractor_class = CustomFeatureExtractor, 
        features_extractor_kwargs = None, 
        normalize_images = False, 
        optimizer_class = th.optim.Adam, 
        optimizer_kwargs = None
    ):
        super().__init__(
            observation_space, 
            action_space, 
            lr_schedule, 
            net_arch, 
            activation_fn, 
            ortho_init, 
            use_sde, 
            log_std_init, 
            full_std, 
            sde_net_arch, 
            use_expln, 
            squash_output, 
            features_extractor_class, 
            features_extractor_kwargs, 
            normalize_images, 
            optimizer_class, 
            optimizer_kwargs
        )
        possible_actions = int(observation_space['actions'].high[0])
        self.padding_idx = action_space.n
        self.action_embedder = nn.Embedding(possible_actions, self.mlp_extractor.latent_dim_pi, padding_idx=self.padding_idx)

    def _build(self, lr_schedule):
        super()._build(lr_schedule)
        self.action_net = nn.Identity()

    def forward(self, obs, deterministic=False):
        """
        Forward pass in all the networks (actor and critic)

        :param obs: Observation
        :param deterministic: Whether to sample or use deterministic actions
        :return: action, value and log probability of the action
        """
        # Preprocess the observation if needed
        features = self.extract_features(obs)
        latent_pi, latent_vf = self.mlp_extractor(features)
        
        obs_actions = obs['actions'].type(th.int)
        action_embeddings = self.action_embedder(obs_actions)
        latent_pi = th.bmm(action_embeddings, latent_pi.unsqueeze(2)).squeeze()
        # print("Actions:", obs_actions)
        # Mask out actions corresponding to padding

        latent_pi = th.where(obs_actions == self.padding_idx, th.tensor(-1e10), latent_pi)
        # print("Latent PI:", latent_pi)

        # Evaluate the values for the given observations
        values = self.value_net(latent_vf)
        distribution = self._get_action_dist_from_latent(latent_pi)
        actions = distribution.get_actions(deterministic=deterministic)
        # print("Selected Action:", actions)
        log_prob = distribution.log_prob(actions)
        # print("Log_Prob:", log_prob)
        actions = actions.reshape((-1,) + self.action_space.shape)
        return actions, values, log_prob

    def evaluate_actions(self, obs, actions):
        """
        Evaluate actions according to the current policy,
        given the observations.

        :param obs:
        :param actions:
        :return: estimated value, log likelihood of taking those actions
            and entropy of the action distribution.
        """
        # Preprocess the observation if needed
        features = self.extract_features(obs)
        latent_pi, latent_vf = self.mlp_extractor(features)

        obs_actions = obs['actions'].type(th.int)
        action_embeddings = self.action_embedder(obs_actions)

        latent_pi = th.bmm(action_embeddings, latent_pi.unsqueeze(2)).squeeze()

        latent_pi = th.where(obs_actions == self.padding_idx, th.tensor(-1e10), latent_pi)

        distribution = self._get_action_dist_from_latent(latent_pi)
        log_prob = distribution.log_prob(actions)
        values = self.value_net(latent_vf)
        return values, log_prob, distribution.entropy()
    
    def get_distribution(self, obs):
        """
        Get the current policy distribution given the observations.

        :param obs:
        :return: the action distribution.
        """

        features = self.extract_features(obs)
        latent_pi = self.mlp_extractor.forward_actor(features)
        obs_actions = obs['actions'].type(th.int)
        action_embeddings = self.action_embedder(obs_actions)
        latent_pi = th.bmm(action_embeddings, latent_pi.unsqueeze(2)).squeeze()
        # Mask out actions corresponding to padding
        latent_pi = th.where(obs_actions == self.padding_idx, th.tensor(-1e10), latent_pi)
        return self._get_action_dist_from_latent(latent_pi)