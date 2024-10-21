import numpy as np 

class time_series_multiperiodic : 
    def __init__(self, type):
        assert type in ['ts', 'mutli_periodic'], 'type must be either ts or multi_periodic'
        self.type = type
    
    if type == 'ts' :
        def values_time_series(self, t, T):
            assert len(t) == len(T), 't and T must have the same length'
            L=np.zeros(len(t),2)
            for i in range(len(t)):
                L[i,0]=t[i]
                L[i,1]=T[i]
            self.time_series = L

    if type == 'multi_periodic' :
        def create_mutiperiodic_signal(self, offset=12, duration, step, amplitude, period):
            assert len(amplitude)==len(period), 'amplitude and period must have the same length'
            assert duration%step==0, 'duration must be a multiple of step'
            