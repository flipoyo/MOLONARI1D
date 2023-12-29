from MOLO_45 import test_SM
import numpy as np
import matplotlib.pyplot as plt

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
Nl = 2
#two layers separated by a 10 cm thick interlayer
#the second layer stops at at depth of 1 m
borders = np.array([0.15,0.25,1],dtype=np.double)
#three main measures at the depths of 10, 20 and 30 cm
depths_meas = np.array([0.1,0.2,0.3],dtype=np.double)
#layer parameters
Ll = np.array([3,3],dtype=np.double)
Cl = np.array([4*10**(6),4*10**(6)],dtype=np.double)
Kl = np.array([10**(-5),10**(-7)],dtype=np.double)
Sl = np.array([0.2,0.2],dtype=np.double)
#initial hydraulic and thermal conditions
H0 = 0.025*np.ones(N,dtype=np.double)
T0 = 295*np.ones(N,dtype=np.double)
#number of times at which H and T must be predicted
ntimes = 1
times = np.array([24*3600],dtype=np.double)
t02 = 0
#solver time step (adapted if autostep)
step = 0.1
#error control parameters if autostep
atol_H = 10**(-6)
rtol_H = 10**(-4)
atol_T = 10**(-6)
rtol_T = 10**(-4)

#solving discretized equations
result = test_SM(N,h,Hriv,Haq,Triv,Taq,Ntimes,dt,t0,tf,Nl,borders,depths_meas,Ll,Cl,Kl,Sl,H0,T0,ntimes,times,t02,step,atol_H,rtol_H,atol_T,rtol_T,autostep=True)

#displaying hydraulic charge curve
plt.plot(np.linspace(0,h,N),result[0,:N])
plt.ylabel('hydraulic charge [m]')
plt.xlabel('depth [m]')
plt.show()

#displaying temperature curve
plt.figure()
plt.plot(np.linspace(0,h,N),result[0,N:],color='red')
plt.ylabel('temperature [K]')
plt.xlabel('depth [m]')
plt.show()