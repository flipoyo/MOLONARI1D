from dataclasses import dataclass
from typing import Sequence

from .params import Param
from .layers import Layer



@dataclass
class State:
    layers: Sequence[Layer]
    energy: float
    ratio_accept: float
    sigma2_temp: float
