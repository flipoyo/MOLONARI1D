import numpy as np
from typing import Sequence

from pyheatmy.core import Column
from pyheatmy.gen_test import Time_series
from pyheatmy.layers import Layer, layersListCreator
from pyheatmy import LAMBDA_W, RHO_W, C_W

class Analy_Sol:
    "Compute the value of temperature based on the analytical solution."
    def __init__( 
        self,
        column_exp : Column,
        time_series : Time_series,
        monolayer : Layer,
        nb_cells : int,
    ):
        self._depth_sensors = column_exp.depth_sensors
        self._real_z_sensors = column_exp._real_z

        self._nb_cells = nb_cells
        self._dz = self._real_z_sensors[-1] / self._nb_cells
        self._z_solve = self._dz/2 + np.array([k*self._dz for k in range(self._nb_cells)])
        self._id_sensors = [np.argmin(np.abs(z - self._z_solve)) for z in column_exp._real_z[1:-1]]

        self._real_t = time_series._time_array
        self._dH = time_series._param_dH[2]
        self._amp_T_river = time_series._param_T_riv[0]
        self._period = time_series._param_T_riv[1]
        self._T_moy = time_series._param_T_riv[2] # il faut mettre une exception si on T_riv_offset différent de T_aq_offset

        self._k_permeability = 10**(-monolayer.params[0])
        self._n = monolayer.params[1]

        self._lambda_s = monolayer.params[2]
        self._rho_cs = monolayer.params[3]
        
        self._lambda_m = (self._n * (LAMBDA_W) ** 0.5 + (1.0 - self._n) * (self._lambda_s) ** 0.5) ** 2
        self._rho_cm = self._n * RHO_W * C_W + (1 - self._n) * self._rho_cs
        
        self._alpha = (RHO_W*C_W/self._rho_cm)*self._k_permeability
        self._kappa = self._lambda_m/self._rho_cm

        self._v_t = -self._alpha*self._dH/self._dz
        self._a_cond = np.sqrt(np.pi/(self._kappa*self._period))

        self._a = None
        self._b = None

        self.analy_temp_general = np.array([None])
        self.analy_temp_cond = np.array([None])

    @classmethod
    def from_dict(cls, analy_sol_dict):
        return cls(**analy_sol_dict)
    
    def compute_a(self):
        self._a = (np.sqrt((np.sqrt(self._v_t**4 + (8*np.pi*self._kappa/self._period)**2) + self._v_t**2)/2) - self._v_t)/(2*self._kappa)

    def compute_b(self): 
        self._b = np.sqrt((np.sqrt(self._v_t**4 + (8*np.pi*self._kappa/self._period)**2) - self._v_t**2)/2)/(2*self._kappa)

    def compute_temp_general(self):
        # on maj les valeurs de a et b
        self.compute_a()
        self.compute_b()
        self.analy_temp_general = np.zeros((self._nb_cells,len(self._real_t)))
        for i, t in enumerate(self._real_t) :      
            self.analy_temp_general[:,i] = self._T_moy + self._amp_T_river*np.exp(-self._a*self._z_solve)*np.sin(2*np.pi*t/self._period - self._b*self._z_solve)


    def compute_temp_cond(self):
        self.analy_temp_cond = np.zeros((self._nb_cells,len(self._real_t)))
        for i, t in enumerate(self._real_t) : 
            self.analy_temp_cond[:,i] = self._T_moy + self._amp_T_river*np.exp(-self._a_cond*self._z_solve)*np.sin(2*np.pi*t/self._period - self._a_cond*self._z_solve)

            
    def generate_RMSE_analytical(self, time_series, column, monolayer): #column défini à partir de time_series
        """This function computes the RMSE of the direct model compared to analytical solutions on simple boundary
        conditions and in a monolayer case"""
        layer_list=layersListCreator([(monolayer.name, monolayer.zLow,*monolayer.params)])
        
        nb_sensors = len(self._id_sensors) # Number of sensors (except boundary conditions : river and aquifer)
        nb_times = len(time_series._time_array)   # Number of times for which we have measures
        if self.analy_temp_general.any()==None :
            self.compute_temp_general()
        #pour les solutions modèle direct, il faut une condition initiale égale à celle du modèle analytique
        
        time_series._T_Shaft[0]=np.array([self.analy_temp_general[id_sens,0] for id_sens in self._id_sensors] + [self.analy_temp_cond[-1,0]])  
        column._T_measures[0]=time_series._T_Shaft[0][:-1]
        time_series._measures_column_one_layer(column, layer_list, self._nb_cells)

        self.temp_shaft_analy = np.zeros((nb_times,nb_sensors))
        for i,id_sens in enumerate(self._id_sensors):
            self.temp_shaft_analy[:,i]=self.analy_temp_general[id_sens,:] #ne contient pas la boundary condition aquifer
        # Array of RMSE for each sensor
        list_RMSE = np.array([np.sqrt(np.sum(self.temp_shaft_analy[:,i] - time_series._T_Shaft[:,i])**2) / nb_times
                             for i in range(nb_sensors)])

        # Total RMSE
        total_RMSE = np.sqrt(np.sum(list_RMSE**2) / nb_sensors)

        return np.append(list_RMSE, total_RMSE)