from MOLO_45 import test_MCMC
import numpy as np
import matplotlib.pyplot as plt
import time

#number of main cells
N = 10
#ground layer height [m]
h = 0.4
#constant boundary parameters
Hriv = np.array([0.05,0.05],dtype=np.double)
Haq = np.array([0,0],dtype=np.double)
Triv = np.array([300,300],dtype=np.double)
Taq = np.array([290,290],dtype=np.double)
#number of samples provided for boundary parameters
Ntimes = 2
#sampling start
t0 = 0
#sampling end
tf = 3600
#sampling step
dt = tf
#number of layers
Nl = 1
#a layer 1 meter thick
borders = np.array([1],dtype=np.double)
#three main measures at the depths of 10, 20 and 30 cm
depths_meas = np.array([0.1,0.2,0.3],dtype=np.double)
#number of MCMC chains
nb_chains = 5
#nb of walk steps
nb_iter = 1000
#predictions after a week
times = np.array([7*24*3600],dtype = np.double)
t0_solve = 0
#constant parameters for random generators of DREAMS
cn = 0.01
c = 0.1
#number of ordered pairs used to compute dX in DREAMS
np_opairs = 2
#number of crossover probabilities
nCR = 10
#physical parameters ranges
range_L = np.array([2,4],dtype = np.double)
range_C = 10**(6)*np.array([3,5],dtype = np.double)
range_K = np.array([10**(-8),10**(-4)],dtype = np.double)
range_S = np.array([0.1,0.3],dtype = np.double)
range_sigma = np.array([0.01,0.4],dtype = np.double)
#error control parameters if autostep
atol_H = 10**(-6)
rtol_H = 10**(-4)
atol_T = 10**(-6)
rtol_T = 10**(-4)

#Steady State solution
def SS(h,depths_meas,Hriv,Haq,Triv,Taq,
       k_ref=10**(-5),
       lambda_ref=3,
       c_ref=4*10**(6),
       s_ref=0.2,
       cw = 4180.,
       rhow = 1000.):
    H_exact = (Haq[0]-Hriv[0])/h*depths_meas+Hriv[0]
    gamma = -cw*rhow*k_ref*(Haq[0]-Hriv[0])/(h*lambda_ref)
    alpha = (Triv[0]-Taq[0])/(1-np.exp(gamma*h))
    beta = (Taq[1]-Triv[0]*np.exp(gamma*h))/(1-np.exp(gamma*h))
    Tmeas = np.exp(gamma*depths_meas)*alpha+beta
    Tmeas = Tmeas.reshape(1,len(Tmeas))
    Tmeas = Tmeas.astype(np.double)
    return Tmeas
#simulated measures
meas = SS(h,depths_meas,Hriv,Haq,Triv,Taq)

#MCMC at work
t0 = time.time()
past = test_MCMC(N,h,Hriv,Haq,Triv,Taq,Ntimes,dt,t0,tf,Nl,borders,depths_meas,nb_chains,nb_iter,0,meas,times,t0_solve,cn,c,np_opairs,nCR,range_L,range_C,range_K,range_S,range_sigma,atol_H,rtol_H,atol_T,rtol_T,autostep=False)
t1 = time.time()
print(f'execution time  = {t1-t0} s')

#computing the average permeability encountered in the random walk
Kpast = np.empty(nb_chains*nb_iter)
for i in range(nb_iter):
    for j in range(nb_chains):
        Kpast[i*nb_chains+j] = past[i,5*j+3]
print(f'average K = {np.average(Kpast)} m^2')

#displaying logarithmic permeability histogram
plt.hist(-np.log10(Kpast),bins=30)
plt.axvline(x=5,color='red')
plt.xlabel('-log10(K)')
plt.ylabel('density')
locs, _ = plt.yticks()
plt.yticks(locs,np.round(locs/len(Kpast),3))
plt.show()