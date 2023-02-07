import gym
import torch as th
from torch import nn
import math
import numpy as np

from gym import spaces

from stable_baselines3.common.torch_layers import BaseFeaturesExtractor, FlattenExtractor
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.preprocessing import get_action_dim

from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy

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
    def __init__(self, observation_space, map_dims) -> None:
        super().__init__()
        self.map_dims = map_dims

        feature_conv1x1 = {}
        feature_count = 0
        for key, space in observation_space.spaces.items():
            feature_channels = 0
            if len(space.shape) >= 2:
                feature_channels += math.prod(space.shape[:-2])
            else:
                feature_channels += math.prod(space.shape)
            
            feature_conv1x1[key] = nn.Sequential(
                nn.Conv2d(feature_channels, 32, kernel_size=1),
                nn.LeakyReLU()
            )
            feature_count += 1

        self.feature_conv1x1 = nn.ModuleDict(feature_conv1x1)
        self.final_conv1x1 = nn.Conv2d(feature_count * 32, 128, kernel_size=1)
    
    def forward(self, observation):
        combined_encoded_obs = []
        for key, obs in observation.items():
            
            if obs.ndim-1 >= 3:
                out = obs.flatten(start_dim=1, end_dim=-3)
            elif obs.ndim-1 < 2:
                out = obs.unsqueeze(-1).unsqueeze(-1).repeat([1, 1, self.map_dims[0], self.map_dims[1]])
            else:
                out = obs.unsqueeze(1)
                
            out = self.feature_conv1x1[key](out)
            combined_encoded_obs.append(out)
        
        features = th.cat(combined_encoded_obs, dim=1)
        features = self.final_conv1x1(features)
        return features

class RescaleLayer(nn.Module):
    def __init__(self, low, high):
        super().__init__()
        self.low = low
        self.high = high

    def forward(self, input):
        return th.div(th.sub(input, self.low), self.high - self.low)

class EmbeddingLayer(nn.Module):
    def __init__(self, num_embeddings, embedding_dim):
        super().__init__()
        self.embedder = nn.Embedding(num_embeddings, embedding_dim)
    
    def forward(self, input):
        out = self.embedder(input.long())
        out = th.movedim(out, -1, 1)
        return out

class CustomFeatureExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space):
        super().__init__(observation_space, features_dim=1)

        self.map_dims = observation_space['terrain_stars'].shape[-2:]
        
        self.resnet = nn.Sequential(
            InputEncoder(observation_space, self.map_dims),
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
        out = self.resnet(observations).flatten(start_dim=1)
        return out

class CustomActorCriticPolicy(MaskableActorCriticPolicy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, features_extractor_class=CustomFeatureExtractor ,**kwargs)

    def extract_features(self, obs):
        return self.features_extractor(obs)