from enum import Enum


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


# param par défaut dans time_series.py
DEFAULT_H_amp = 0.1
DEFAULT_steady = CODE_scalar
DEFAULT_H_offset = 0.05
DEFAULT_dH_signal = [DEFAULT_H_amp, DEFAULT_steady, DEFAULT_H_offset]

DEFAULT_T_amp = 5
DEFAULT_T_period = NDAYINMONTH*NSECINDAY
DEFAULT_T_riv_offset = 20
DEFAULT_T_aq_offset = 12

DEFAULT_T_riv_signal = [DEFAULT_T_amp, DEFAULT_T_period, DEFAULT_T_riv_offset]
DEFAULT_T_aq_signal = [DEFAULT_T_amp, DEFAULT_steady, DEFAULT_T_aq_offset]

DEFAULT_sigmaP = CODE_scalar
DEFAULT_sigmaT = CODE_scalar

DEFAULT_time_step = 15  # 15mn
DEFAULT_period = 1  # 1j

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

class DeviceType(Enum):
    PRESSURE = 1
    TEMPERATURE = 2

# Dictionary mapping SensorType to file names
DEVICE_FILE_NAMES = {
    DeviceType.PRESSURE: 'P',
    DeviceType.TEMPERATURE: 'T'
}


class ClassType(Enum):
    COLUMN = 1
    TIME_SERIES = 2

# Dictionary mapping SensorType to file names
CLASS_FILE_NAMES = {
    ClassType.COLUMN: 'measures', #I would prefer "BY_COLUMN"
    ClassType.TIME_SERIES: 'by_device', #I would prefer "BY_DEVICE"
}


class SensorType(Enum):
    pressure_sensors = 1
    shafts = 2
    temperature_sensors = 3


# Dictionary mapping SensorType to file names
SENSOR_FILE_NAMES = {
    SensorType.pressure_sensors: 'Pvirtual',
    SensorType.shafts: 'Svirtual',
    SensorType.temperature_sensors: 'Tvirtual'
}