"""
    author: Nicolas Matte
    session: MOLONARI 2023
"""

# This file contains all the tools about intelligent
# RAM management

# They will be integrated in Molonari 2024.

# You need to use these functions before computing MCMC
# so as to resolve memory issues.

# imports
import numpy as np
import psutil

def ram_estimation(nb_iter, nb_chain, nb_cells, nb_times, nb_layer, nb_param=4, n_sous_ech_iter=10, n_sous_ech_space=1, n_sous_ech_time=1, nb_bytes=4):
    """
    Input : le nombre d'itérations, de chaînes, de cellules, de couches,
            les pas de sous-échantillonnage respectivement pour les itérations MCMC,
            l'espace et le temps
            nb_bytes est la taille en octets d'un élément de tableau, par exemple 4 pour float32
    Output : estimation de la mémoire vive recquise pour réaliser les inversions MCMC
    Method : calcule la RAM nécessaire pour stocker les arrays et y ajoute x % (à déterminer)
    """
    nb_iter_sous_ech = int( np.ceil( (nb_iter+1) / n_sous_ech_iter))
    nb_cells_sous_ech = int( np.ceil(nb_cells / n_sous_ech_space) )
    nb_times_sous_ech = int( np.ceil(nb_times / n_sous_ech_time) )



    ram = 0 # initialisation
    ram += (4*nb_chain+1)*nb_cells*nb_times # _temp_act, temp_old, temp_new, _flow_act, _flow_old
    ram += 2*nb_chain # _energy, _energy_old
    ram += nb_cells*nb_times # temp_new
    ram += nb_iter*nb_chain # acceptance
    ram += (nb_iter+1)*nb_chain*nb_layer*nb_param # _params
    ram += (nb_chain+2)*nb_layer*nb_param #x_new, X_new et dX
    ram += 2*nb_iter_sous_ech*nb_chain*nb_cells_sous_ech*nb_times_sous_ech # _flows, _temp
    ram += 6*nb_cells_sous_ech*nb_times_sous_ech # quantiles_temps, quantiles_flows

    ram *= 1.3 # Correction (the model can be improved)

    return ram*nb_bytes


def propose_n_iter_sous_ech(nb_iter, nb_chain, nb_cells, nb_times, nb_layer, n_sous_ech_space=1, n_sous_ech_time=1, nb_bytes=4, threshold = 2*1024**3):
    """
    Input : MCMC parameters
    Output : suggestion of value for n_iter_sous_ech
    """
    n_sous_ech_iter = 10
    while ram_estimation(nb_iter, nb_chain, nb_cells, nb_times, nb_layer, n_sous_ech_iter, n_sous_ech_space, n_sous_ech_time, nb_bytes) > threshold:
        n_sous_ech_iter += 1
    print(f"You should use n_sous_ech_iter = ", n_sous_ech_iter)
    return n_sous_ech_iter

def warning_ram(nb_iter, nb_chain, nb_cells, nb_times, nb_layer, n_sous_ech_iter=10, n_sous_ech_space=1, n_sous_ech_time=1, nb_bytes=4):
    """
    Input : Parameters of MCMC
    Output : Bool - Do we compute MCMC ?
             Parameters - if bool, parameters used in the MCMC we are about to compute.
    """
    ram_est = ram_estimation(nb_iter, nb_chain, nb_cells, nb_times, nb_layer, n_sous_ech_iter, n_sous_ech_space, n_sous_ech_time, nb_bytes) # estimation de la RAM utilisée par MCMC
    ram_available = psutil.virtual_memory().available # available ram of the computer

    # Output initialisation
    b = True # Bool - Do we compute MCMC ?

    if ram_est > 2e9:
        while True:
            user_input = input(f"// WARNING - The given parameters recquire {ram_est/(1024**3)} > 2Go RAM for the MCMC inversions \\ \n Input 0 if you want to continue anyway \n Input 1 if you want the computer to automatically choose the parameters in order to be under 2Go RAM \n Input 2 if you want to stop the algorithm.")
            print(f"// WARNING - The given parameters recquire {ram_est/1e9} > 2Go RAM for the MCMC inversions \n Input 0 if you want to continue anyway \n Input 1 if you want the computer to automatically choose the parameters in order to be under 2Go RAM \n Input 2 if you want to stop the algorithm.")

            # Check whether the input is valid
            if user_input in ('0', '1', '2'):
                break
            else:
                print("Invalid. Please input 0; 1 ou 2.")

        if user_input == 0:
            # Continue anyway
            pass
        elif user_input == 1:
            # Compute parameters in order to use less than 2Go RAM for the MCMC inversions.
            n_sous_ech_iter = propose_n_iter_sous_ech(nb_iter, nb_chain, nb_cells, nb_times, nb_layer, n_sous_ech_space, n_sous_ech_time, nb_bytes)        
        else:
            # Stop the algorithm
            b = False
        
    # Computer available RAM constraint
    ram_est = ram_estimation(nb_iter, nb_chain, nb_cells, nb_times, nb_layer, n_sous_ech_iter, n_sous_ech_space, n_sous_ech_time, nb_bytes) # estimation de la RAM utilisée par MCMC
    if ram_est >= ram_available:
        while True:
            print(f"// WARNING - The new parameters recquire {ram_est/(1024**3)} Go while the available RAM is {ram_available/(1024**3)} Go.",
                "Do you want me to compute a new value for n_iter_sous_ech ?",
                sep="\n")
            user_input = input("0 : Yes \n 1 : No")

            # Check whether the input is valid
            if user_input in ('0', '1'):
                break
            else:
                print("Invalid. Please input 0 ou 1.")
        
        if user_input == 0:
            # Compute parameters in order to use less than ram_available RAM for the MCMC inversions.
            threshold = ram_available - ram_est - 100*1024**2 # Let 100 extra Mo in order not to break the computer.
            n_sous_ech_iter = propose_n_iter_sous_ech(nb_iter, nb_chain, nb_cells, nb_times, nb_layer, n_sous_ech_space, n_sous_ech_time, nb_bytes, threshold)
        else:
            # Stop the algorithm
            b = False
    
    return b, [nb_iter, nb_chain, nb_cells, nb_times, nb_layer, n_sous_ech_iter, n_sous_ech_space, n_sous_ech_time, nb_bytes]
