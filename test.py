import numpy as np
import function_conv

tf = 1*24*3600
Tss = np.array([290.,300.])
Hss = np.array([0.05,0.])
htot = 0.4
N = 22
T0 = 295*np.ones(N)
H0 = 0.025*np.ones(N)
tol = 10**(-1)

result = function_conv.call_homogeneous(tf,Tss,Hss,N,T0,H0,tol)