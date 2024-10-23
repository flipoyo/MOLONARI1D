@classmethod
class molonari1D:
    def __init__(self,
        simulType=FORWARDMODEL, # à mettre dans config avec MCMC et MULTIMCMC
        river_bed: float ,  # profondeur de la colonne en mètres
        depth_sensors: Sequence[float], # profondeur des capteurs de températures en mètres
        offset: float,  # correspond au décalage du capteur de température par rapport au lit de la rivière
        dH_measures: list, # liste contenant un tuple avec la date, la charge et la température au sommet de la colonne
        T_measures: list,  # liste contenant un tuple avec la date et la température aux points de mesure de longueur le nombre de temps mesuré
        sigma_meas_P: float,  # écart type de l'incertitude sur les valeurs de pression capteur
        sigma_meas_T: float,  # écart type de l'incertitude sur les valeurs de température capteur
        inter_mode: str = "linear", # mode d'interpolation du profil de température initial : 'lagrange' ou 'linear'
        eps=EPSILON,
        layerList = [("Couche 1", DEFAULT_DEPTH, DEFAULTmoinsLogIntrinK, DEFAULTN, lambda_s, rhos_cs)],
        rac="~/OUTPUT_MOLONARI1D/generated_data", #printing directory by default,

        verbose=False):

        self.column = Column(river_bed,depth_sensors,offset,dH_measures,T_measures,sigma_meas_P,sigma_meas_T,inter_mode,eps,rac,verbose)
        self.simylType = simulType
        self.Layerslist = layersListCreator(layerList)
        self.nparam = 
        self.nlayer = 
        on initialise les prior des instance de param à None

        #Puis creer correctement les instanciations de layer et param basé sur la list

    def init_prior(self,Prior):
        
    def calculate_molonari1D(self):
        if self.simylType==FORWARDMODEL:
            self.column.compute_solve_transi()#les arguments sont maintenant dans self
        else 
            self.column.compute_mcmc()    
