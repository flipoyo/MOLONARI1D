from dataclasses import dataclass
from typing import Sequence

from pyheatmy.params import Param
from pyheatmy.layers import Layer


@dataclass
class StateOld:
    '''deprecated version, no stratification'''
    params: Param
    energy: float
    ratio_accept: float
    sigma2_temp: float = None


@dataclass
class State:
    layers: Sequence[Layer]
    energy: float
    ratio_accept: float
    sigma2_temp: float
