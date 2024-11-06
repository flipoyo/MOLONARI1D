    def burning_DREAM():
        for i in trange(nb_iter, desc="Burn in phase"):
            std_X = np.std(X, axis=0)  # calcul des écarts types des paramètres
            for j in range(nb_chain):
                x_new = np.zeros((nb_layer, nb_param))
                dX = np.zeros((nb_layer, nb_param))  # perturbation DREAM
                if typealgo=="no sigma":
                    new_sigma2_temp=sigma2
                else :
                    new_sigma2_temp=sigma2_temp_prior.perturb(current_sigma2[j])

                x_new=self.sampling_DREAM(nb_chain,nb_layer, nb_param, X, dX,x_new, j, delta, ncr, c, c_star, cr_vec, pcr, ranges)[0]
                id=self.sampling_DREAM(nb_chain,nb_layer, nb_param, X, dX,x_new, j, delta, ncr, c, c_star, cr_vec, pcr, ranges)[1]                                                                                                               

                # Calcul du profil de température associé aux nouveaux paramètres
                self.compute_solve_transi(
                    convert_to_layer(nb_layer, name_layer, z_low, x_new),
                    nb_cells,
                    verbose=False,
                )
                temp_new = (
                    self.get_temperatures_solve()
                )  # récupération du profil de température

                energy_new = compute_energy_mcmc(
                    temp_new[ind_ref], temp_ref, remanence, new_sigma2_temp, sigma2_distrib
                )  # calcul de l'énergie

                # calcul de la probabilité d'accpetation
                log_ratio_accept = compute_log_acceptance(
                    energy_new, _energy_burn_in[i][j]
                )

                # Acceptation ou non des nouveaux paramètres
                if np.log(np.random.uniform(0, 1)) < log_ratio_accept:
                    X[j] = x_new  # actualisation des paramètres pour la chaine j
                    _temp_iter[j] = temp_new  # actualisation du profil de température
                    _flow_iter[j] = self.get_flows_solve()  # actualisation du débit
                    _energy_burn_in[i + 1][j] = energy_new  # actualisation de l'énergie
                    current_sigma2[j] = new_sigma2_temp  # actualisation de sigma2_temp
                else:
                    dX = np.zeros((nb_layer, nb_param))
                    _energy_burn_in[i + 1][j] = _energy_burn_in[i][j]  # on garde la même énergie
                    current_sigma2[j] = current_sigma2[j]  # on garde la même sigma2_temp

                # Mise à jour des paramètres de la couche j pour DREAM
                for l in range(nb_layer):
                    J[l, id] += np.sum((dX[l] / std_X[l]) ** 2)
                    n_id[l, id] += 1
            
            # Mise à jour du pcr pour chaque couche pour DREAM
            for l in range(nb_layer):
                pcr[l][n_id[l] != 0] = J[l][n_id[l] != 0] / n_id[l][n_id[l] != 0]
                pcr[l] = pcr[l] / np.sum(pcr[l])

            # Actualisation des paramètres à la fin de l'itération
            _params[i + 1] = X
            # Fin d'une itération, on check si on peut sortir du burn-in
            if gelman_rubin(i + 2, nb_param, nb_layer, _params[: i + 2], threshold=threshold):
                if verbose:
                    print(f"Burn-in finished after : {nb_burn_in_iter} iterations")
                break  # on sort du burn-in
            nb_burn_in_iter += 1  # incrémentation du numbre d'itération de burn-in
        self.nb_burn_in_iter = nb_burn_in_iter

    def burning_single_chain():
        for i in trange(nb_iter, desc="Burn in phase"): #nb_iter échantillonnage et n retient celui dnt l'energie est min
            init_layers = all_priors.sample()
            init_sigma2_temp = sigma2_temp_prior.sample() #on a déjà intialisé une fois auparavant --> voir si on peut o^timiser
            self.compute_solve_transi(init_layers, nb_cells, verbose=False)
            self._states.append(
                State(
                    layers=init_layers,
                    energy=compute_energy(
                        self.temperatures_solve[ind_ref, :],
                        sigma2=init_sigma2_temp,
                        sigma2_distrib=sigma2_temp_prior.density,
                    ),
                    ratio_accept=1,
                    sigma2_temp=init_sigma2_temp,
                )
            )
        self._initial_energies = [state.energy for state in self._states]
        self._states = [min(self._states, key=attrgetter("energy"))]
        self._acceptance = np.zeros(nb_iter)

        _temperatures[0] = self.get_temperatures_solve()
        _flows[0] = self.get_flows_solve()

        nb_accepted = 0

        current_sigma2=[]        #def current_sigma2[j] et son state associé
        X=[state.layers for state in self._states]
        initial_state=self._states
        #faut qu'en sortie j'ai mon X de défini


    @checker
    def compute_mcmc(
            self,
            all_priors: Union[
                AllPriors,
                Sequence[
                    Union[
                        LayerPriors,
                        Sequence[Union[str, float, Sequence[Union[Prior, dict]]]],
                    ]
                ],
            ],
            nb_cells: int,
            quantile: Union[float, Sequence[float]] = (QUANTILE_MIN,MEDIANE,QUANTILE_MAX),
            verbose=False,
            typealgo="no sigma",
            nb_iter=NITMCMC,
            nb_chain=10,
            delta=3,  #nombre de chaînes qu'on croise
            ncr=3,    #nombre max de paramètres qu'on va perturber en même temps dans une itération de DREAM
            c=0.1,
            c_star=1e-12,
            remanence = 1,
            n_sous_ech_iter=10,
            n_sous_ech_space=1,
            n_sous_ech_time=1,
            threshold=1.2
        ):

            process = psutil.Process()

            if typealgo=="no sigma":
                sigma2 = DEFAULT_SIGMA2_T
                sigma2_distrib=None
            else :
                sigma2_temp_prior = Prior((SIGMA2_MIN_T, SIGMA2_MAX_T), RANDOMWALKSIGMAT, lambda x: 1 / x)
                sigma2_distrib = sigma2_temp_prior.density

            # vérification des types des arguments
            if isinstance(quantile, Number):
                quantile = [quantile]

            if not isinstance(all_priors, AllPriors):
                all_priors = AllPriors([LayerPriors(*conv(layer)) for layer in all_priors])

            # définition des paramètres de la simulation
            dz = self._real_z[-1] / nb_cells
            _z_solve = dz / 2 + np.array([k * dz for k in range(nb_cells)])
            ind_ref = [np.argmin(np.abs(z - _z_solve)) for z in self._real_z[1:-1]]
            temp_ref = self._T_measures[:, :].T

            # quantités des différents paramètres
            nb_layer = len(all_priors)  # nombre de couches
            nb_param = N_PARAM_MCMC  # nombre de paramètres à estimer par couche
            nb_accepted = 0  # nombre de propositions acceptées
            nb_burn_in_iter = 0  # nombre d'itération de burn-in

            # création des bornes des paramètres
            ranges = np.empty((nb_layer, nb_param, 2))
            for l in range(nb_layer):
                for p in range(nb_param):
                    ranges[l, p] = all_priors[l][p].range

            # propriétés des couches
            name_layer = [all_priors.sample()[i].name for i in range(nb_layer)]
            z_low = [all_priors.sample()[i].zLow for i in range(nb_layer)]

            _temp_iter = np.zeros(
                (nb_chain, nb_cells, len(self._times)), np.float32
            )  # dernière température acceptée pour chaque chaine
            _flow_iter = np.zeros(
                (nb_chain, nb_cells, len(self._times)), np.float32
            )  # dernier débit accepté pour chaque chaine

            _energy_burn_in = np.zeros((nb_iter + 1, nb_chain), np.float32)  # énergie pour le burn-in

            # variables pour l'état courant
            temp_new = np.zeros(
                (nb_cells, len(self._times)), np.float32
                                )
            energy_new = 0
            X = np.array([np.array(all_priors.sample()) for _ in range(nb_chain)])
            X = np.array(
                [
                    np.array([X[c][l].params for l in range(nb_layer)])
                    for c in range(nb_chain)
                ]
            )  # stockage des paramètres pour l'itération en cours

            # stockage des résultats
            self._states = list()  # stockage des états à chaque itération
            self._acceptance = np.zeros((nb_chain,), np.float32)  # stockage des taux d'acceptation

            _params = np.zeros(
                (nb_iter + 1, nb_chain, nb_layer, nb_param), np.float32
            )  # stockage des paramètres
            _params[0] = X  # initialisation des paramètres

            # objets liés à DREAM
            cr_vec = np.arange(1, ncr + 1) / ncr
            n_id = np.zeros((nb_layer, ncr), np.float32)
            J = np.zeros((nb_layer, ncr), np.float32)
            pcr = np.ones((nb_layer, ncr)) / ncr          #probabilité que ncr prenne la valeur 1, ou 2,... ou ncr

            if verbose:
                print(
                    "--- Compute DREAM MCMC ---",
                    "Priors :",
                    *(f"    {prior}" for prior in all_priors),
                    f"Number of cells : {nb_cells}",
                    f"Number of iterations : {nb_iter}",
                    f"Number of chains : {nb_chain}",
                    "--------------------",
                    sep="\n",
                )

            def compute_energy_mcmc(temp1,temp2, remanence,sigma2, sigma2_distrib):
                    if sigma2_distrib is None:
                        return(compute_energy(temp1,temp2,remanence, sigma2))
                    else :
                        return(compute_energy_with_distrib(temp1,temp2,sigma2,sigma2_distrib))
            

            # initialisation des chaines
            init_sigma2=[]
            for j in range(nb_chain):
                self.compute_solve_transi(
                    convert_to_layer(nb_layer, name_layer, z_low, X[j]),
                    nb_cells,
                    verbose=False,
                )
                _temp_iter[j] = self.get_temperatures_solve()
                _flow_iter[j] = self.get_flows_solve()
                if typealgo=="no sigma":
                    init_sigma2.append(sigma2)
                    _energy_burn_in[0][j] = compute_energy_mcmc(
                    _temp_iter[j][ind_ref], temp_ref, remanence, sigma2,sigma2_distrib
                    )
                else:
                    init_sigma2_temp = sigma2_temp_prior.sample()
                    init_sigma2.append(init_sigma2_temp)
                    _energy_burn_in[0][j] = compute_energy_mcmc(_temp_iter[j][ind_ref], temp_ref, remanence, init_sigma2_temp,sigma2_distrib)


            print(f"Initialisation - Utilisation de la mémoire (en Mo) : {process.memory_info().rss /1e6}")

            current_sigma2=init_sigma2
            if verbose:
                print("--- Begin Burn in phase ---")
            if nb_chain=1:
                burning_single_chain()
            else:
                burning_DREAM()


            # Transition après le burn in
            del _params  # la variable _params n'est plus utile

            # Préparation du sous-échantillonnage
            nb_iter_sous_ech = int( np.ceil( (nb_iter+1) / n_sous_ech_iter))
            nb_cells_sous_ech = int( np.ceil(nb_cells / n_sous_ech_space) )
            nb_times_sous_ech = int( np.ceil(len(self._times) / n_sous_ech_time) )

            # Initialisation des flux
            _flows = np.zeros(
                (nb_iter_sous_ech, nb_chain, nb_cells_sous_ech, nb_times_sous_ech), np.float32
            )  # initisaliton du flow
            _flows[0] = _flow_iter[
                :, ::n_sous_ech_space, ::n_sous_ech_time
            ]  # initialisation du flow

            _temp = np.zeros(
                (nb_iter_sous_ech, nb_chain, nb_cells_sous_ech, nb_times_sous_ech), np.float32
                )
            _temp[0] = _temp_iter[:, ::n_sous_ech_space, ::n_sous_ech_time]  # initialisation des températures sous-échantillonnées

            # initialisation des états
            if nb_chain=1:
                init_sigma2_temp = current_sigma2[0]
                initial_state=burning_single_chain()[]
                self._states.append(initial_state)
                
            for j in range(nb_chain):
                init_sigma2_temp = current_sigma2[j]
                self._states.append(
                    State(
                        layers=convert_to_layer(nb_layer, name_layer, z_low, X[j]),
                        energy=_energy_burn_in[
                            min(nb_burn_in_iter + 1, len(_energy_burn_in) - 1)
                        ][j],
                        ratio_accept=1,
                        sigma2_temp=init_sigma2_temp,
                    )
                )

            print(f"Initialisation post burn-in - Utilisation de la mémoire (en Mo) : {process.memory_info().rss /1e6}")


            for i in trange(nb_iter, desc="DREAM MCMC Computation", file=sys.stdout):
                # Initialisation pour les nouveaux paramètres
                std_X = np.std(X, axis=0)  # calcul des écarts types des paramètres
                for j in range(nb_chain):
                    x_new = np.zeros((nb_layer, nb_param), np.float32)
                    dX = np.zeros((nb_layer, nb_param), np.float32)  # perturbation DREAM
                    if typealgo=="no sigma":
                        new_sigma2_temp=sigma2
                    else :
                        new_sigma2_temp=sigma2_temp_prior.perturb(current_sigma2[j])
                    if nb_chain>1:
                        x_new=self.sampling_DREAM(nb_chain,nb_layer, nb_param, X, dX,x_new, j, delta, ncr, c, c_star, cr_vec, pcr, ranges)[0]
                        id=self.sampling_DREAM(nb_chain,nb_layer, nb_param, X, dX,x_new, j, delta, ncr, c, c_star, cr_vec, pcr, ranges)[1]                                                                                                   
                    else:
                        x_new=self.sample_random_walk( nb_layer,X,x_new,j, all_priors)

                    # Calcul du profil de température associé aux nouveaux paramètres
                    self.compute_solve_transi(
                        convert_to_layer(nb_layer, name_layer, z_low, x_new),
                        nb_cells,
                        verbose=False,
                    )
                    temp_new = (
                        self.get_temperatures_solve()
                    )  # récupération du profil de température

                    energy_new = compute_energy_mcmc(
                        temp_new[ind_ref], temp_ref, remanence,new_sigma2_temp,sigma2_distrib
                    )  # calcul de l'énergie

                    # calcul de la probabilité d'accpetation
                    log_ratio_accept = compute_log_acceptance(
                        energy_new, self._states[-nb_chain].energy
                    )

                    # Acceptation ou non des nouveaux paramètres
                    if np.log(np.random.uniform(0, 1)) < log_ratio_accept:
                        X[j] = x_new
                        current_sigma2[j]= new_sigma2_temp

                        _temp_iter[j] = temp_new

                        _flow_iter[j] = self.get_flows_solve()

                        if (i+1) % n_sous_ech_iter == 0: 
                            # Si i+1 est un multiple de n_sous_ech_iter, on stocke
                            k = (i+1) // n_sous_ech_iter
                            _temp[k, j] = temp_new[::n_sous_ech_space, ::n_sous_ech_time]
                            _flows[k, j] = _flow_iter[j, ::n_sous_ech_space, ::n_sous_ech_time]

                        nb_accepted += 1
                        self._acceptance[j] += 1
                        self._states.append(
                            State(
                                layers=convert_to_layer(nb_layer, name_layer, z_low, x_new),
                                energy=energy_new,
                                ratio_accept=nb_accepted / (i * nb_chain + j + 1),
                                sigma2_temp=current_sigma2[j],
                            )
                        )
                    else:
                        dX = np.zeros(
                            (nb_layer, nb_param), np.float32
                            )
                        current_sigma2[j] = current_sigma2[j]
                        if (i+1) % n_sous_ech_iter == 0:
                            # Si i+1 est un multiple de n_sous_ech_iter, on stocke
                            k = (i+1) // n_sous_ech_iter
                            _temp[k][j] = _temp_iter[j][
                            ::n_sous_ech_space, ::n_sous_ech_time
                        ]
                            _flows[k][j] = _flow_iter[j][
                            ::n_sous_ech_space, ::n_sous_ech_time
                        ]

                        self._states.append(
                            State(
                                layers=self._states[-nb_chain].layers,
                                energy=self._states[-nb_chain].energy,
                                ratio_accept=nb_accepted / (i * nb_chain + j + 1),
                                sigma2_temp=current_sigma2[j],
                            )
                        )  # ajout de l'état à la liste des états

                    # Mise à jour des paramètres de la couche j pour DREAM
                    if nb_chain>1:
                        for l in range(nb_layer):
                            J[l, id] += np.sum((dX[l] / std_X[l]) ** 2)
                            n_id[l, id] += 1

            # Calcul des quantiles pour la température
            _temp = _temp.reshape(nb_iter_sous_ech * nb_chain, nb_cells_sous_ech, nb_times_sous_ech)
            _flows = _flows.reshape(nb_iter_sous_ech * nb_chain, nb_cells_sous_ech, nb_times_sous_ech)

            # print("Occupation mémoire des températures (en Mo) : ", _temp.nbytes/1e6)
            # print("Occupation mémoire des flux (en Mo) : ", _flows.nbytes/1e6)

            print(f"Fin itérations MCMC, avant le calcul des quantiles - Utilisation de la mémoire (en Mo) : {process.memory_info().rss /1e6}")

            self._quantiles_temperatures = {
                quant: res
                for quant, res in zip(quantile, np.quantile(_temp, quantile, axis=0))
            }
            
            self._quantiles_flows = {
                quant: res
                for quant, res in zip(quantile, np.quantile(_flows, quantile, axis=0))
            }

            self._acceptance = self._acceptance / nb_iter

            if verbose:
                print("Quantiles computed")