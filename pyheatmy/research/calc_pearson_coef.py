import sklearn as sk
import numpy as np
from pyheatmy.synthetic_MOLONARI import *
from pyheatmy.time_series_multiperiodic import *
from pyheatmy.utils import *
from pyheatmy.config import *
from pyheatmy.core import *
from pyheatmy import layersListCreator
import scipy as sp

# Test
# Paramètres

T_riv = time_series_multiperiodic("multi_periodic")
T_MOY_ANNUELLE = 12 + ZERO_CELSIUS # °C, représente l'offset commun de nos signaux de température
T_AMP_ANNUELLE = 6 # °C, représente l'amplitude de variation de température annuelle
T_AMP_JOURNALIERE = 1 # °C, représente l'amplitude de variation de température journalière

P_an = 12 # Période annuelle en mois
P_jour = 24 # Période journalière, en heures

t_debut = (2024, 4, 15, 8, 0, 0)  # (year, month, day, hour, minute, second)
t_fin = (2024, 10, 15, 8, 0, 0)
dt = int(NSECINHOUR / 4)  #On se place dans le cas d'un point de mesure toutes les heures (à moduler en fonction de l'intervale temporel considéré)


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

def plot_pearson_coef(pearson_coef, dates, dt):
    n_days = nb_days_in_period(dates, dt)
    n_days = np.arange(n_days)
    plt.scatter(n_days, pearson_coef)
    plt.xlabel('Jours')
    plt.ylabel('Coefficient de Pearson')
    plt.ylim(-1, 1)
    plt.title('Evolution du coefficient de Pearson en fonction du temps')
    plt.show()


def pearson_coef_test(offset_H, moinslog10IntrinK): 
    """Conditions limites"""
    # Température de la rivière
    zeroT = ZERO_CELSIUS  #time_series works only with forcings in celsius. See if it is deeper in pyheatmy or not

    T_riv_amp = 5
    T_riv_offset = 20  + zeroT
    nday = 3
    P_T_riv = nday*NHOURINDAY*4*dt #monthly   period
    # Température de l'aquifère
    T_aq_amp = 0
    T_aq_offset = 14 + zeroT
    P_T_aq = -9999 # à mettre dans le init
    # Pression différentielle
    dH_amp = 0
    P_dh = -9999 #14*24*4*dt


    depth_sensors = [.1, .2, .3, .4]
    Zbottom = 0.4

    """Bruit de mesure"""
    sigma_meas_P = 0.001  #initial value 0.001
    sigma_meas_T = 0.1  # initial value 0.1
    time_series_dict_user1 = {
    "offset":.0,
    "depth_sensors":depth_sensors,
	"param_time_dates": [t_debut, t_fin, dt], 
    "param_dH_signal": [dH_amp, P_dh, offset_H], #En vrai y aura une 4e valeur ici mais ca prendra en charge pareil
	"param_T_riv_signal": [T_riv_amp, P_T_riv, T_riv_offset],
    "param_T_aq_signal": [T_aq_amp, P_T_aq, T_aq_offset],
    "sigma_meas_P": sigma_meas_P,
    "sigma_meas_T": sigma_meas_T, 
}
    emu_observ_test_user1 = synthetic_MOLONARI.from_dict(time_series_dict_user1)
    
    T_riv.create_multiperiodic_signal([T_AMP_ANNUELLE, T_AMP_JOURNALIERE], [[P_an, 'm'], [P_jour, 'h']], emu_observ_test_user1._dates, dt,
                                   offset=T_MOY_ANNUELLE)
    emu_observ_test_user1._T_riv = T_riv.multi_periodic[1][:]

    emu_observ_test_user1._generate_Shaft_Temp_series()
    emu_observ_test_user1._generate_perturb_Shaft_Temp_series()
    emu_observ_test_user1._generate_perturb_T_riv_dH_series()
    name ="Couche en sable"
    zLow = Zbottom
    n = 0.1
    lambda_s = 2 # test cas purement advectif
    rhos_cs = 4e6

    # modèle une couche
    layers_list= layersListCreator([(name, zLow, moinslog10IntrinK, n, lambda_s, rhos_cs)])

    print(f"Layers list: {layers_list}")

    # on utilise les mesures générées précédemment dans les init "dH_measures" et "T_measures"
    col_dict = {
        "river_bed": 1., 
        "depth_sensors": depth_sensors, #En vrai y aura une 4e valeur ici mais ca prendra en charge pareil
        "offset": .0,
        "dH_measures": emu_observ_test_user1._molonariP_data,
        "T_measures": emu_observ_test_user1._molonariT_data,
        "sigma_meas_P": 0.001, #float
        "sigma_meas_T": 0.1, #float
    }
    col = Column.from_dict(col_dict,verbose=False)
    nb_cells=20 # nombre de cellules, une tous les 5 centimètres 

    col._compute_solve_transi_multiple_layers(layers_list, nb_cells, verbose=True)
    depth_cells = np.array([depth_sensors[-1]/nb_cells*i for i in range(nb_cells)])
    pears_coef=get_pearson_coef(depth_cells, np.transpose(col._temperatures), emu_observ_test_user1._dates, dt)
    plot_pearson_coef(pears_coef, emu_observ_test_user1._dates, dt)


if __name__ == '__main__':
    pearson_coef_test(0.05, 12)