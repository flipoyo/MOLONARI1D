"""
This file regroups different messages the backend and frontend can use to communicate.
Enumerations are used as a nicer way to evaluate the state of a system. Instead of using an error code (ex: error 404), we use a pretty little text.
"""
from enum import Enum, unique, auto

@unique
class ComputationsState(Enum):
    RAW_MEASURES = auto()
    CLEANED_MEASURES = auto()
    DIRECT_MODEL = auto()
    MCMC = auto()

@unique
class CleanupStatus(Enum):
    NONE = auto()
    IQR = auto()
    ZSCORE = auto()
