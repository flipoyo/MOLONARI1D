from enum import Enum

import numpy as np

# temporal values
NSECINMIN = 60
NSECINHOUR = 3600
NSECINDAY = 86400
NHOURINDAY = 24
NDAYINYEAR = 365
NDAYINMONTH = 30
ABSURD_DATE = "1999/09/09  09:09:09"

# valeurs absurdes par défaut
CODE_Temp = 959595
CODE_scalar = -9999

# param par défaut dans prior
PARAMBOUND = 1e7

# param par défaut dans time_series.py
DEFAULT_H_amp = 0.1
DEFAULT_steady = CODE_scalar
DEFAULT_H_offset = 0.05
DEFAULT_dH_signal = [DEFAULT_H_amp, DEFAULT_steady, DEFAULT_H_offset]

DEFAULT_T_amp = 5
DEFAULT_T_period = NDAYINMONTH * NSECINDAY
DEFAULT_T_riv_offset = 20
DEFAULT_T_aq_offset = 12

DEFAULT_T_riv_signal = [DEFAULT_T_amp, DEFAULT_T_period, DEFAULT_T_riv_offset]
DEFAULT_T_aq_signal = [DEFAULT_T_amp, DEFAULT_steady, DEFAULT_T_aq_offset]

DEFAULT_sigmaP = CODE_scalar
DEFAULT_sigmaT = CODE_scalar

DEFAULT_time_step = 15  # 15mn
DEFAULT_period = 1  # 1j

# prior initialisation

MOINSLOG10INTRINK_INTERVAL = (11, 15)
MOINSLOG10INTRINK_SIGMA = 0.01
MOINSLOG10INTRINK_DEFAULT = 13

N_INTERVAL = (0.01, 0.25)
N_SIGMA = 0.01
N_DEFAULT = 0.05

LAMBDA_S_INTERVAL = (1, 5)
LAMBDA_S_SIGMA = 0.1
LAMBDA_S_DEFAULT = 2.5


RHOS_CS_INTERVAL = (1e6, 1e7)  # Ensure PARAMBOUND is defined in config.py
RHOS_CS_SIGMA = 1e5
RHOS_CS_DEFAULT = 5e6

DEFAULT_SIGMA2_T = 1.0
SIGMA2_MIN_T = 0.001
SIGMA2_MAX_T = 1.0
RANDOMWALKSIGMAT = 0.01

Q_INTERVAL = (1e-9, 1e-5)
Q_SIGMA = 1e-10
Q_DEFAULT = 0

# param par défaut dans pyheatmy.py
DEFAULT_sensor_depth = [0.1, 0.2, 0.3, 0.4]

LAMBDA_W = 0.6071
RHO_W = 1000
C_W = 4185
ALPHA = 0.4
G = 9.81
EPSILON = 1e-10
N_UPDATE_MU = 96
MU = 1e-3
MU_W = 1e-3
ZERO_CELSIUS = 273.15
QUANTILE_MIN = 0.05
MEDIANE = 0.5
QUANTILE_MAX = 0.95
N_PARAM_MCMC = 5
GAMMA_FACTOR = 2.38


class DeviceType(Enum):
    PRESSURE = 1
    TEMPERATURE = 2


# Dictionary mapping SensorType to file names
DEVICE_FILE_NAMES = {DeviceType.PRESSURE: "P", DeviceType.TEMPERATURE: "T"}


class ClassType(Enum):
    COLUMN = 1
    TIME_SERIES = 2


# Dictionary mapping SensorType to file names
CLASS_FILE_NAMES = {
    ClassType.COLUMN: "measures",  # I would prefer "BY_COLUMN"
    ClassType.TIME_SERIES: "by_device",  # I would prefer "BY_DEVICE"
}


class SensorType(Enum):
    pressure_sensors = 1
    shafts = 2
    temperature_sensors = 3


# Dictionary mapping SensorType to file names
SENSOR_FILE_NAMES = {
    SensorType.pressure_sensors: "Pvirtual",
    SensorType.shafts: "Svirtual",
    SensorType.temperature_sensors: "Tvirtual",
}

# MCMC parametrization
NITMCMC = 150

# Coefficients of the Mu equation
MU_A = 1.856e-11 * 1e-3
MU_B = 4209
MU_C = 0.04527
MU_D = -3.376e-5
DEFAULT_MU = 1e-3

# VALEURS
NB_CELLS = 100
GELMANRCRITERIA = 1.2
PARAM_LIST = ("moinslog10IntrinK", "n", "lambda_s", "rhos_cs", "q") #a priori sigma2 a un statut particulier