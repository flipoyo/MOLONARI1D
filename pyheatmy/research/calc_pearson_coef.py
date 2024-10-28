import sklearn as sk
import numpy as np
from pyheatmy.synthetic_MOLONARI import *
from pyheatmy.time_series_multiperiodic import *
from pyheatmy.utils import *
from pyheatmy.config import *
from pyheatmy.core import *
from pyheatmy import layersListCreator
import scipy as sp

def nb_per_day(dt, Verbose = True):
    if Verbose:
        print('dt must be in seconds')
    return(int(NSECINDAY/dt))


def nb_days_in_period(dates, dt):
    return int(dates.shape[0]/nb_per_day(dt))


# Argument : la matrice, un jour donné et la période journalière à regarder 
# Sortie : liste des amplitudes sur ce jour donné
def amplitude(T, day, n_dt_in_day):
    amplitude_list = []
    for j in range(len(T[0,:])):
        T_max = max(T[day:day + n_dt_in_day,j])
        T_min = min(T[day: day + n_dt_in_day,j])
        A = (T_max - T_min) / 2
        amplitude_list.append(A)
    return amplitude_list


# Retourne ln(rapport des amplitudes) en fonction de la profondeur en un jour donné
def ln_amp(T, day, n_dt_in_day):
    amplitude_list = amplitude(T, day, n_dt_in_day)
    amplitude_array = np.array(amplitude_list)
    ln_rapport_amplitude = np.log( amplitude_array / amplitude_array[0] )
    return ln_rapport_amplitude


def get_pearson_coef(depths, temperatures, dates, dt):
    n_dt_in_day = nb_per_day(dt)
    n_days = nb_days_in_period(dates, dt)
    pearson_coef = np.zeros(n_days)
    for i in range(n_days):
        ln_amp_i = ln_amp(temperatures, i*n_dt_in_day, n_dt_in_day)
        Lr = sp.stats.linregress(depths, ln_amp_i)
        pearson_coef[i] = Lr.rvalue
    return pearson_coef