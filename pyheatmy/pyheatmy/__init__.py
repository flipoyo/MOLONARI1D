# param par défaut dans gen_test.py
DEFAULT_dH = [1, 24 * 3600, 10]
DEFAULT_T_riv = [30, 24 * 3600, 20]
DEFAULT_T_aq = [30, 24 * 3600, 12]
DEFAULT_time_step = 15  # 15mn
DEFAULT_period = 1  # 1j

LAMBDA_W = 0.6071
RHO_W = 1000
C_W = 4185

# valeur absurdre par défaut
CODE_Temp = 959595
CODE_list_sensors = [0.1, 0.2, 0.3, 0.4]
CODE_scalar = -9999

from .core import Column
from .params import Param, Prior
from .checker import ComputationOrderException
from .layers import layersListCreator, Layer
from .gen_test import Time_series
from .val_analy import Analy_Sol
