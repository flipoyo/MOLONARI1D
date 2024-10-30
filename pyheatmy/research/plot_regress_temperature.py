import matplotlib.pyplot as plt
import numpy as np
import scipy
from sklearn import linear_model
import calc_pearson_coef as cpc
from pyheatmy.core import *
from pyheatmy.time_series_multiperiodic import class_time_series_multiperiodic
from pyheatmy import *
import matplotlib.dates as mdates

# Argument : la matrice, liste des profondeur
# Sortie : liste des amplitudes
def amplitude(T):
    amplitude_list = []
    for j in range(len(T[0,:])):
        T_max = max(T[:,j])
        T_min = min(T[:,j])
        A = (T_max - T_min) / 2
        amplitude_list.append(A)
    return amplitude_list


# Retourne ln(rapport des amplitudes) en fonction de la profondeur
def ln_amp(T):
    amplitude_list = amplitude(T)
    amplitude_array = np.array(amplitude_list)
    ln_rapport_amplitude = np.log( amplitude_array / amplitude_array[0] )
    return ln_rapport_amplitude


# Trace le ln_temp(T) en fonction de depths
def plot_ln_amp(depths, T):
    y = ln_amp(T)
    plt.plot(depths, y)
    plt.title("Logarithme du rapport des amplitudes")
    plt.xlabel("profondeur (unit)")
    plt.ylabel("ln(A_z / A_0)")
    plt.show()


# Renvoie l'instance de régression linéaire des données (profondeur, ln(rapport amplitudes))
def linear_regression(depths, T):
    y = ln_amp(T)
    return scipy.stats.linregress(depths, y)


# Trace l'interpolation linéaire en imprimant le coefficient d'exactitude
def plot_linear_regression(depths, T):
    # assert len(T) == lent(depths), "a temperature measure must be assigned to a single depth"
    X = depths.reshape(-1,1)
    Y = ln_amp(T)
    Lr = linear_regression(depths, T)
    Pearson_coefficient = Lr.rvalue
    slope = Lr.slope
    intercept = Lr.intercept
    lm = linear_model.LinearRegression()
    lm.fit(X, Y)
    plt.scatter(X, Y, color="r", marker="o", s=10)
    y_pred = lm.predict(X)
    plt.plot(X, y_pred, color="k")
    plt.xlabel("profondeur (unit)")
    plt.ylabel("ln(A_z / A_0)")
    plt.title("Régression linéaire sur le rapport des logarithmes des amplitudes")
    plt.figtext(.6, .8, "y = " + str(round(slope,2)) + "x + " + str(round(intercept,2)))
    plt.figtext(.6, .7, "Pearson coefficient : " + str(round(Pearson_coefficient,2)))
    plt.show()


# Mosaïque des différentes courbes en fonction des valeurs de k (list_K = liste de ces valeurs)
# T est la liste des matrices de températures pour différentes valeurs de k
def plot_mosaic(depths, list_T, list_K):  
    # assert len(list_T[0]) == lent(depths), "a temperature measure must be assigned to a single depth"
    assert len(list_T) == len(list_K), 'The number of k values does not match the number a temperature matrices'
    n_rows = len(list_K)//2 + len(list_K)%2
    fig, ax = plt.subplots(n_rows, ncols=2, constrained_layout = True)
    X = np.array(depths).reshape(-1,1)
    for i in range(n_rows):
        for j in range(2):
            if 2*i + j < len(list_K):
                Y = ln_amp(list_T[2*i+j])
                Lr = linear_regression(depths, list_T[2*i+j])
                Pearson_coefficient = Lr.rvalue
                slope = Lr.slope
                intercept = Lr.intercept
                lm = linear_model.LinearRegression()
                lm.fit(X, Y)
                ax[i][j].scatter(X, Y, color="r", marker="o", s=10)
                y_pred = lm.predict(X)
                ax[i][j].plot(X, y_pred, color="k")
                ax[i][j].set_xlabel('profondeur (unit)')
                ax[i][j].set_ylabel('log(A_z / A_0)')
                ax[i][j].set_title('Rapport des ln(A_z / A_0) avec -log(k) =' + str(list_K[2*i + j]), size = 10)   
                ax[i][j].text(0.9, 0.9, "Pearson coefficient : " + str(round(Pearson_coefficient,2)), transform=ax[i][j].transAxes, ha='right', va='top')
    plt.show()


# Mosaïque des différentes courbes en fonction des valeurs de k (list_K = liste de ces valeurs)
# list_T est la liste des matrices de températures pour différentes valeurs de k
def plot_mosaic_pearson(cut_depths, list_T, list_K, dates, dt):  
    assert len(list_T[0][0,:]) == len(cut_depths), "a temperature measure must be assigned to a single depth, and len(depths) = " + str(len(cut_depths)) + ', len(temperature_depths) = ' + str(len(list_T[0][0,:]))
    assert len(list_T) == len(list_K), 'The number of k values does not match the number a temperature matrices'
    n_rows = len(list_K)//2 + len(list_K)%2
    fig, ax = plt.subplots(n_rows, ncols=2, constrained_layout = True)
    n_days = cpc.nb_days_in_period(dates, dt, verbose = False)
    n_days = np.arange(n_days)
    X = n_days
    for i in range(n_rows):
        for j in range(2):
            if 2*i + j < len(list_K):
                Y = cpc.get_pearson_coef(cut_depths, list_T[2*i+j], dates, dt)
                ax[i][j].scatter(X, Y, color="r", marker="o", s=30)
                ax[i][j].set_xlabel('day')
                ax[i][j].set_ylabel('Pearson coefficient')
                ax[i][j].set_title('Pearson par jour avec -log(k) = ' + str(list_K[2*i + j]), size = 10)   
                ax[i][j].set_ylim(-1,1) 
    plt.show()



# On commence par créer un signal d'entrée grace à la classe time_series_multiperiodic, que l'on forcera dans la classe Synthetic_Molonari ensuite

T_riv = class_time_series_multiperiodic("multi_periodic")

# On regarde des variations de température sur une année, on définit une période journalière, et une période annuelle

"""Conditions limites"""
# Température de la rivière
T_riv_year_amp = 5 # °C, représente l'amplitude de variation de température annuelle
T_riv_offset = 12 + ZERO_CELSIUS # °C, représente l'offset commun de nos signaux de température
T_riv_day_amp = 5 # °C, représente l'amplitude de variation de température journalière
# Température de l'aquifère
T_aq_amp = 0
T_aq_offset = 12 + ZERO_CELSIUS
P_T_aq = -9999 # à mettre dans le init

P_T_riv_year = NDAYINYEAR * NSECINDAY # Période annuelle en mois
P_T_riv_day = NSECINDAY # Période journalière, en heures
t_debut = (2024, 4, 15, 8, 0, 0)  # (year, month, day, hour, minute, second)
t_fin = (2024, 4, 20, 8, 0, 0)
dt = int(NSECINHOUR / 4)  #On se place dans le cas d'un point de mesure toutes les quinze minutes (à moduler en fonction de l'intervale temporel considéré)

moinslog10IntrinK = 11
lambda_s = 2 # test cas purement advectif
rhos_cs = 4e6
range_of_minus_log_10_K = [10,11,12,13,14,15]  # The values we want to test

n = 0.1  # porosité
nb_cells=100 # nombre de cellules, une tous les 5 centimètres 
depth_sensors = [.1, .2, .3, .4]
Zbottom = 1
river_bed = 1.  # profondeur de la colonne en mètres
last_cell = int(9/10 * nb_cells)  # on écarte les dernières valeurs pour éviter les effets de bord
depth_cells = np.linspace(0, river_bed, nb_cells)

# Pression différentielle
dH_amp = 0
dH_offset = 0.1  # m
P_dh = -9999 #14*24*4*dt

# Bruit de mesure
sigma_meas_P = 0.001
sigma_meas_T = 0.1

name ="Couche en sable"


#On définit une fonction pour pouvoir compiler en faisant varier la valeur de la charge (et donc le régime infiltration ou exfiltration vers la 
#rivière) ainsi que la valeur de la porosité (et donc le régime de diffusion de la chaleur - majoritairement diffusif ou advectif)

def profil_temperature(offset_H, moinslog10IntrinK, verbose = False): 
    time_series_dict_user1 = {
    "offset":.0,
    "depth_sensors": depth_sensors,
	"param_time_dates": [t_debut, t_fin, dt], 
    "param_dH_signal": [dH_amp, P_dh, offset_H], #En vrai y aura une 4e valeur ici mais ca prendra en charge pareil
	"param_T_riv_signal": [T_riv_day_amp, P_T_riv_day, T_riv_offset],
    "param_T_aq_signal": [T_aq_amp, P_T_aq, T_aq_offset],
    "sigma_meas_P": sigma_meas_P,
    "sigma_meas_T": sigma_meas_T, 
    "verbose" : verbose
}
    emu_observ_test_user1 = synthetic_MOLONARI.from_dict(time_series_dict_user1)
    
    T_riv.create_multiperiodic_signal([T_riv_year_amp, T_riv_day_amp], [[P_T_riv_year, 's'], [P_T_riv_day, 's']], emu_observ_test_user1._dates, dt,
                                   offset=T_riv_offset, verbose = False)
    
    emu_observ_test_user1._T_riv = T_riv.multi_periodic[1][:]

    emu_observ_test_user1._generate_Shaft_Temp_series(verbose = False)
    emu_observ_test_user1._generate_perturb_Shaft_Temp_series()
    emu_observ_test_user1._generate_perturb_T_riv_dH_series()

    # modèle une couche
    layers_list= layersListCreator([(name, Zbottom, moinslog10IntrinK, n, lambda_s, rhos_cs)])

    # print(f"Layers list: {layers_list}")  # dans verbose

    # on utilise les mesures générées précédemment dans les init "dH_measures" et "T_measures"
    col_dict = {
        "river_bed": river_bed, 
        "depth_sensors": depth_sensors, #En vrai y aura une 4e valeur ici mais ca prendra en charge pareil
        "offset": .0,
        "dH_measures": emu_observ_test_user1._molonariP_data,
        "T_measures": emu_observ_test_user1._molonariT_data,
        "sigma_meas_P": sigma_meas_P,
        "sigma_meas_T": sigma_meas_T,
    }
    col = Column.from_dict(col_dict,verbose=False)
    col._compute_solve_transi_multiple_layers(layers_list, nb_cells, verbose=False)
    return col._temperatures


def list_k_T(list_of_minus_log_K):
    T_list = []
    for l in list_of_minus_log_K:
        T_list.append(np.transpose(profil_temperature(dH_offset, l)[0:last_cell,:]))
    return T_list


# Function that plots the pearson coefficient day by day
def data_plot_pearson(point_number, verbose = True):
    # url = path MOLONARI1D\dataAnalysis\data_traite\
    url = 'dataAnalysis\data_traite\point' + str(point_number) + '_temperature_traité.csv'
    df = pd.read_csv(url)
    df.columns = ['Date_heure', 'T_Sensor0', 'T_Sensor1', 'T_Sensor2', 'T_Sensor3']
    if verbose:
        print(df.head())

    # Create the temperature matrix
    T = [df['T_Sensor' + str(i)] for i in range(4)]
    T = np.array(T)
    T = np.transpose(T)

    depths = np.linspace(0, 0.4, 4)

    # prt.plot_linear_regression(depths, T)
    Y = cpc.get_pearson_coef(depths, T, df['Date_heure'], dt)
    n_days = cpc.nb_days_in_period(df['Date_heure'], dt)
    n_days = np.arange(n_days)
    X = n_days

    plt.scatter(X, Y)
    plt.title('Pearson coefficient for Point' + str(point_number))
    plt.xlabel('day')
    plt.ylabel('Pearson coefficient')
    plt.show()


# Possible improvements of the function :
# - verbose to display all the possible numbers of the point
# Mosaic for different points

# plot on the same graph for the different depths temperatures as a function of time 
def plot_data(point_number, verbose = True):
    url = 'dataAnalysis\data_traite\point' + str(point_number) + '_temperature_traité.csv'
    df = pd.read_csv(url)
    df.columns = ['Date_heure', 'T_Sensor0', 'T_Sensor1', 'T_Sensor2', 'T_Sensor3']
    df['Date_heure'] = pd.to_datetime(df['Date_heure'], dayfirst = True)

    # Tracer toutes les colonnes sauf 'Date_heure' en fonction de 'Date_heure'
    df.set_index('Date_heure').plot(figsize=(10, 6), grid=True, title="Graphique des valeurs en fonction des dates")
    plt.xlabel("Date")
    plt.ylabel("Température (°C)")
    plt.title("signal de température pour le capteur " + str(point_number))
    plt.show()

if __name__ == '__main__':
    plot_data(53)