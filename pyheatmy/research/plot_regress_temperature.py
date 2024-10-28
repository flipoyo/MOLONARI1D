import matplotlib.pyplot as plt
import numpy as np
import scipy
from sklearn import linear_model
import calc_pearson_coef as cpc

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
    X = np.array(depths).reshape(-1,1)
    Y = ln_amp(T)
    Lr = linear_regression(X, T)
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


def list_k_T(list_of_minus_log_K):
    T_list = []
    for l in list_of_minus_log_K:
        T_list.append(temperature_K(l))
    return list_of_minus_log_K, T_list