# Application Programming Interface - 2022
## Projet MOLONARI

## Introduction

Cette bibliothèque spécifie les interfaces d’échanges entre les trois pôles capteurs, calculs et IHM afin de mener le projet à bien.

***

## IHM vers Calcul

Cette partie décrit les informations que l'IHM doit envoyer à Calcul pour définir les objets et utiliser les méthodes de calcul principales.

Les seuls objets que l'IHM a besoin de définir sont :
* Les instances de la classe **`Column`**.
* Les instances de la classe **`Layer`**.
* Les instances de la classe **`Prior`**.

### Classe `Prior`

* **Définition d’un objet Prior :**
    * **Paramètres :**
        * `range` : `tuple`, intervalle dans lequel le paramètre peut varier.
        * `sigma` : `float`, écart type de la gaussienne utilisée pour la marche aléatoire pour ce paramètre.
        * `density` : `callable`, densité de la loi a priori. Par défaut, c’est une fonction constante, correspondant à une loi uniforme.
    * **Remarque :** L'utilisateur a potentiellement besoin de définir lui-même un `Prior` pour la MCMC avec estimation du paramètre `sigma2`.

### Classe `Layer`

* **Définition d’un objet Layer :**
    * **Paramètres :**
        * `name` : `string`
        * `zLow` : `float`, profondeur en m du bas de la couche (repère orienté du haut vers le bas).
        * `moinslog10K` : `float`, valeur de $-\log_{10}(K)$ où $K$ est la perméabilité.
        * `n` : `float`, porosité.
        * `lambda_s` : `float`.
        * `rhos_cs` : `float`.
    * **Exemple :**
        ```python
        my_layer = Layer(“Couche 1”, 0.2, 4.0, 0.1, 2.0, 4e6)
        ```
    * **Remarque :** Le groupe IHM créera des objets de la classe `Layer` uniquement via la fonction `layersListCreator` décrite ci-après.

### Fonction `layersListCreator`

* **Définition d’une liste d’objets de Layer avec la fonction layersListCreator** (ce n'est pas une méthode de la classe `Layer`).
    * **Paramètres :**
        * `layersListInput` : `list`, liste de tuples où chaque tuple contient les six arguments nécessaires à la définition d’un objet `Layer`.
    * **Retourne :**
        * Une liste d’objets de la classe `Layer`.
    * **Exemple :**
        ```python
        my_layer_list = layersListCreator(
            [("Couche 1", 0.1, 4, 0.1, 2, 4e6),
             ("Couche 2", 0.25, 4.2, 0.1, 3, 4e7)]
        )
        ```

### Classe `Column`

* **Définition d’un objet Column avec la méthode de classe `from_dict` :**
    * **Paramètres :** Un dictionnaire de la forme (`clé` : `valeurs`) :
        * `river_bed` : `float`, altitude du lit de la rivière, en m (inutilisé actuellement).
        * `depth_sensors` : `Sequence[float]`, liste des profondeurs des 4 capteurs de la tige, en m.
        * `offset` : `float`, enfoncement excédentaire de la tige, en m.
        * `dH_measures` : `list`, liste de tuples `(date, (charge, température_sommet_colonne))`.
        * `T_measures` : `list`, liste de tuples `(date, array([temp_capteur1, temp_capteur2, ...]))`.
        * `sigma_meas_P` : `float`, erreur de mesure sur la pression (inutilisé actuellement).
        * `sigma_meas_T` : `float`, erreur de mesure sur la température (inutilisé actuellement).
        * `inter_mode` : `str`, type d’interpolation ("linear" par défaut, ou "lagrange").
    * **Retourne :** Objet de type `Column`.
    * **Exemple :**
        ```python
        dH_measures = [
            (Timestamp('2016-06-28 06:45:00'), (0.84556517, 287.165)),
            (Timestamp('2016-06-28 07:00:00'), (0.84559872, 287.159)),
            # ...
        ]

        T_measures = [
            (Timestamp('2016-06-28 06:45:00'), array([287.272, 287.344, 287.272, 287.08 ])),
            (Timestamp('2016-06-28 07:00:00'), array([287.248, 287.32 , 287.272, 287.08 ]))
            # ...
        ]

        col_dict = {
            "river_bed": 1.,
            "depth_sensors": [.1, .2, .3, .4],
            "offset": .0,
            "dH_measures": dH_measures,
            "T_measures": T_measures,
            "sigma_meas_P": None,
            "sigma_meas_T": None,
            "inter_mode": "linear"
        }

        col = Column.from_dict(col_dict)
        ```

* **Appel du modèle direct via la méthode `compute_solve_transi` :**
    * **Paramètres :**
        * `layersList` : Liste d’objets de la classe `Layer` **OU** tuple avec les 4 paramètres (en mode homogène).
        * `nb_cells` : `int`, nombre de cellules de la discrétisation.
        * `verbose` : `booléen`.
    * **Retourne :** Rien (met à jour les attributs de l'objet `Column`).
    * **Exemple :**
        ```python
        # Appel en homogène
        col.compute_solve_transi((4, 0.1, 2, 4e6), 100)

        # Appel en stratifié
        col.compute_solve_transi(my_layer_list, 100)
        ```

* **Calcul de l’inversion bayésienne via la méthode `compute_mcmc` :**
    * **Paramètres :**
        * `nb_iter` : `int`, nombre d’itérations.
        * `all_priors` : `list`, chaque élément est de la forme `[Nom de couche, zLow de la couche, dictionnaire_des_priors]`.
        * `nb_cells` : `int`.
        * `quantile` : `tuple`.
        * `sigma2` : `float`, `None` par défaut. Si `None`, `sigma2` est estimé.
        * `sigma2_temp_prior` : `Prior`, distribution a priori de `sigma2` (utilisée si `sigma2=None`).
    * **Retourne :** Rien (stocke les états de la MCMC).
    * **Exemple (pour une colonne à deux strates) :**
        ```python
        priors_couche_1 = {
            "moinslog10K": ((1.5, 6), .01),
            "n": ((.01, .25), .01),
            "lambda_s": ((1, 5), .1),
            "rhos_cs": ((1e6,1e7), 1e5),
        }

        priors_couche_2 = {
            "moinslog10K": ((1.5, 6), .01),
            "n": ((.01, .25), .01),
            "lambda_s": ((1, 5), .1),
            "rhos_cs": ((1e6,1e7), 1e5),
        }

        all_priors = [
            ["Couche 1", 0.2, priors_couche_1],
            ["Couche 2", 0.4, priors_couche_2]
        ]

        # MCMC sans estimation de sigma2
        col.compute_mcmc(
            nb_iter = 5000,
            all_priors = all_priors,
            nb_cells = 100,
            quantile = (0.05, 0.5, 0.95),
            sigma2 = 1.0
        )

        # MCMC avec estimation de sigma2
        col.compute_mcmc(
            nb_iter = 5000,
            all_priors = all_priors,
            nb_cells = 100,
            quantile = (0.05, 0.5, 0.95),
            sigma2_temp_prior = Prior((0.1, np.inf), 0.1, lambda x : 1/x)
        )
        ```

***

## Calcul vers IHM

Cette partie décrit les méthodes que l'IHM peut utiliser sur un objet de type `Column` pour récupérer des informations issues des méthodes de calcul.

### Méthodes disponibles après un appel du modèle direct

Ces méthodes récupèrent les informations calculées par le **dernier appel** du modèle direct (via `compute_solve_transi` ou `compute_mcmc`).

* **`get_id_sensors()`** : Récupère les indices des cellules contenant un capteur.
    * **Retourne** : `list` des indices des cellules contenant des capteurs (hors rivière et aquifère).
    * **Exemple** : `[24, 49, 74]`

* **`get_RMSE()`** : Récupère les RMSE.
    * **Retourne** : `array` contenant les RMSE pour chaque capteur, puis la RMSE globale.
    * **Exemple** : `array([0.0763115, 0.09875992, 0.04563868, 0.0767243])`

* **`get_depths_solve()`** : Récupère les profondeurs des milieux des cellules.
    * **Retourne** : `array` contenant les profondeurs des milieux des cellules.

* **`get_times_solve()`** : Récupère les temps.
    * **Retourne** : `list` de `Timestamp` (dates des mesures).

* **`get_temps_solve(z=None)`** : Récupère les températures.
    * **Paramètres** : `z` : `float` (optionnel), profondeur à laquelle on souhaite récupérer les températures.
    * **Retourne** :
        * Si `z` est précisé : `array` unidimensionnel (températures au cours du temps à la profondeur `z`).
        * Si `z` n’est pas fourni : tableau bidimensionnel des températures pour toutes les profondeurs (lignes) et tous les temps (colonnes).

* **`get_advec_flows_solve()`** : Récupère les flux advectifs.
    * **Retourne** : `array` bidimensionnel (profondeurs en lignes, dates en colonnes).

* **`get_conduc_flows_solve()`** : Récupère les flux conductifs.
    * **Retourne** : `array` bidimensionnel (profondeurs en lignes, dates en colonnes).

* **`get_flows_solve(z=None)`** : Récupère les débits.
    * **Paramètres** : `z` : `float` (optionnel), profondeur à laquelle on souhaite récupérer les débits.
    * **Retourne** :
        * Si `z` est précisé : `array` unidimensionnel (débits au cours du temps à la profondeur `z`).
        * Si `z` n’est pas fourni : tableau bidimensionnel des débits pour toutes les profondeurs (lignes) et tous les temps (colonnes).

#### Détail données transmis / Return `solve_transi`

Les fonctions ci-dessus (qui doivent être appelées après `compute_solve_transi`) renvoient les données dans les formats suivants :

| Méthode | Contenu | Format/Unité |
| :--- | :--- | :--- |
| `get_depths_solve()` | Liste des profondeurs des milieux des cellules | `numpy.array` (m) |
| `get_times_solve()` | Liste des Temps | `list` de `Timestamp` (s) |
| `get_temps_solve()` | Matrice des températures | `numpy.array` (lignes=profondeur, colonnes=temps, en K) |
| `get_flows_solve()` | Matrice des débits | `numpy.array` (lignes=profondeur, colonnes=temps, en m³.s⁻¹) |
| `get_advec_flows_solve()` | Matrice des flux de chaleurs Advectifs | `numpy.array` (lignes=profondeur, colonnes=temps, en °C.s⁻¹) |
| `get_conduc_flows_solve()` | Matrice des flux de chaleurs Conductifs | `numpy.array` (lignes=profondeur, colonnes=temps, en °C.s⁻¹) |

### Méthodes disponibles après un appel de la MCMC

Ces méthodes ne peuvent pas être utilisées avant d’avoir appelé `compute_mcmc` une première fois.

* **`get_depths_mcmc()`** : Récupère les profondeurs des milieux des cellules.
    * **Retourne** : `array` contenant les profondeurs des milieux des cellules utilisées dans la MCMC.
* **`get_times_mcmc()`** : Récupère les temps.
    * **Retourne** : `list` de `Timestamp` (dates des mesures).
* **`sample_param()`** : Récupère des paramètres aléatoirement.
    * **Retourne** : `list` de `named tuple` (`Parametres`), contenant les 4 paramètres de chaque couche, pour un état de la MCMC choisi aléatoirement.
* **`get_best_sigma2()`** : Récupère le meilleur `sigma2`.
    * **Retourne** : `float` correspondant au `sigma2` du Maximum A Posteriori (MAP, énergie minimale).
* **`get_best_layers()`** : Récupère les meilleurs layers.
    * **Retourne** : `list` de `Layer`, correspondant aux couches du MAP.
* **`get_all_params()`** : Récupère tous les paramètres.
    * **Retourne** : `list` de matrices, où la n-ième matrice correspond au n-ième `Layer` et contient les distributions (4 colonnes) de ce paramètre.
* **`get_all_moinslog10K()` / `get_all_n()` / `get_all_lambda_s()` / `get_all_rhos_cs()`** : Récupère tous les paramètres individuellement.
    * **Retourne** : `list` dont le n-ième élément est une liste contenant les valeurs du paramètre pour chaque layer du n-ième état de la MCMC.
* **`get_all_sigma2()`** : Récupère tous les `sigma2`.
    * **Retourne** : `list` des `sigma2` pour chaque état de la MCMC.
* **`get_all_energy()`** : Récupère toutes les énergies.
    * **Retourne** : `list` des énergies pour chaque état de la MCMC.
* **`get_all_acceptance_ratio()`** : Récupère tous les *acceptance ratio*.
    * **Retourne** : `array` de la proportion d’états acceptés à chaque itération.
* **`get_quantiles()`** : Récupère les quantiles.
    * **Retourne** : Objet contenant les quantiles donnés lors de l'appel de `compute_mcmc`.

* **`get_temps_quantile(quantile)`** : Récupère un quantile de température.
    * **Paramètres** : `quantile` : `float` (doit faire partie de l'argument `quantiles` de `compute_mcmc`).
    * **Retourne** : `array` bidimensionnel des températures pour toutes les profondeurs (lignes) et tous les temps (colonnes).

* **`get_flows_quantile(quantile)`** : Récupère un quantile de débit.
    * **Paramètres** : `quantile` : `float` (doit faire partie de l'argument `quantiles` de `compute_mcmc`).
    * **Retourne** : `array` bidimensionnel des débits pour toutes les profondeurs (lignes) et tous les temps (colonnes).

* **`get_RMSE_quantile(quantile)`** : Récupère la RMSE d’un quantile.
    * **Paramètres** : `quantile` : `float` (doit faire partie de l'argument `quantiles` de `compute_mcmc`).
    * **Retourne** : `array` contenant les RMSE pour chaque capteur, puis la RMSE globale.

#### Détail données transmis / `get_quantile()`

Les fonctions ci-dessus (qui doivent être appelées après `compute_mcmc` avec l'argument `quantile`) renvoient les données dans les formats suivants :

| Méthode | Contenu | Format/Unité |
| :--- | :--- | :--- |
| `get_depths_mcmc()` | Liste des profondeurs | `numpy.array` (m) |
| `get_times_mcmc()` | Liste des temps | `list` de `Timestamp` (s) |
| `get_flows_quantile(0.5)` | Matrices des débits (pour le quantile 50%) | `numpy.array` (lignes=profondeur, colonnes=temps, en m³.s⁻¹) |
| `get_temps_quantile(0.95)` | Matrices des températures (pour le quantile 95%) | `numpy.array` (lignes=profondeur, colonnes=temps, en K) |
| `get_moinslog10K_quantile(0.5)` | Paramètres pour les quantiles (non détaillé dans la doc d'origine) | `numpy.array` |

***

## Générateur des données et visualisation de la solution analytique

Cette partie décrit deux modules : `gen_test.py` pour générer des données et `val_analy.py` pour la solution analytique et la comparaison avec le modèle direct.

### Générateur des données (`gen_test.py`)

* **Définir un objet `time_series()`** : La méthode de classe `Time_series.from_dict()` est utilisée pour l'instanciation.
    * **Paramètres** :
        * `offset`, `depth_sensors` : Similaire à `Column`.
        * `param_time_dates` : `[t_debut, t_fin, dt]` (dates au format `(y,m,d,h,mn,s)`, `dt` en secondes).
        * `param_dH_signal` : `[dH_amp, P_dh, dH_offset]` (pour le signal sinusoïdal de charge).
        * `param_T_riv_signal` : `[T_riv_amp, P_T_riv, T_riv_offset]` (pour la température rivière).
        * `param_T_aq_signal` : `[T_aq_amp, P_T_aq, T_aq_offset]` (pour la température aquifère).
        * `sigma_meas_P`, `sigma_meas_T` : `float` pour simuler le bruit gaussien de mesure.
    * **Retourne** : Un objet `time_series()`.
    * **Exemple :**
        ```python
        """Fenêtre temporelle"""
        t_debut = (2010, 1, 1)
        t_fin = (2010, 5, 30, 23, 59, 59)
        dt = 15*60 # pas de temps en (s)

        """Conditions limites"""
        T_riv_amp = 5
        T_riv_offset = 20 + K_offset
        P_T_riv = 28*24*4*dt
        T_aq_amp = 0
        T_aq_offset = 12 + K_offset
        P_T_aq = -9999
        dH_amp = 0
        dH_offset = 1
        P_dh = -9999

        """Bruit de mesure"""
        sigma_meas_P = 0.5
        sigma_meas_T = 0.5

        """Instanciation de l'objet Time_series"""
        time_series_dict_user1 = {
            "offset":.0,
            "depth_sensors":[.25, .5, .75, 1],
            "param_time_dates": [t_debut, t_fin, dt],
            "param_dH_signal": [dH_amp, P_dh, dH_offset],
            "param_T_riv_signal": [T_riv_amp, P_T_riv, T_riv_offset],
            "param_T_aq_signal": [T_aq_amp, P_T_aq, T_aq_offset],
            "sigma_meas_P": sigma_meas_P,
            "sigma_meas_T": sigma_meas_T,
        }
        emu_observ_test_user1 = Time_series.from_dict(time_series_dict_user1)
        ```

* **`generate_dates_series()`** : Génère les dates des chroniques.
    * **Retourne** : L'objet `time_series` avec les attributs `self._dates` (format `datetime.datetime`) et `self._time_array` (temps en secondes depuis le début) mis à jour.

* **`_generate_dH_series()`** : Génère les chroniques de pression/charge (`self._dH`).
* **`_generate_Temp_riv_series()`** : Génère les chroniques de température de la rivière (`self._T_riv`).
* **`_generate_T_riv_dH_series()`** : Génère le fichier de chroniques de pression/température au sommet, format datalogger (`self._T_riv_dH_measures`).
* **`_generate_Shaft_Temp_series()`** : Génère les chroniques de températures sur les capteurs du shaft, format datalogger (`self._T_shaft_measures`).
* **`_generate_perturb_Shaft_Temp_series()`** : Génère les chroniques du shaft avec perturbations de mesures (`self._T_shaft_measures_perturb`).
* **`_generate_perturb_T_riv_dH_series()`** : Génère les chroniques rivière/charge avec perturbations de mesures (`self._T_riv_dH_measures_perturb`).

* **`_measures_column_one_layer(Coulumn, liste de Layer, nb_cells)`** : Interaction pour mettre à jour l'objet `Column` avec les profils de température calculés par le modèle direct à partir des observations simulées.
    * **Retourne** : Aucun retour, les objets `Column` et `Time_series` sont mis à jour.

### Solution analytique (`val_analy.py`)

#### Formules analytiques

La solution analytique en cas général est :

$$
T(z,t) = \text{Ré} \left[ \theta_R e^{i\omega t} \frac{\left(\frac{\gamma}{h_0} - i \gamma^2 \omega\right) e^{-\gamma z} - \theta_{AQ} e^{i\omega t}}{...} \right]
$$

avec $\gamma, \dots$

La solution analytique en cas conductif est :
...

* **Définir un objet `Analy_Sol()` :**
    * **Paramètres :**
        * `column_exp`
        * `time_series`
        * `monolayer`
        * `nb_cells`
    * **Retourne :** Un objet `analy_sol`.

* **`compute_a()`, `compute_b()`** :
    * **Retourne** : Valeur des coefficients calculés d’après les propriétés hydro-thermiques et la période de signal.

* **`compute_temps_general()`** :
    * **Retourne** : `array` des températures calculées analytiquement en cas général.

* **`compute_temp_cond()`** :
    * **Retourne** : `array` des températures calculées analytiquement en cas conductif.

* **`generate_RMSE_analytical(time_series, colonne_exp, monolayer)`** :
    * **Retourne** : `array` contenant les RMSE du modèle direct par rapport aux solutions analytiques.
    * **Exemple (instanciation objets) :**
        ```python
        """Colonne"""
        col_dict = {
            "river_bed": 1.,
            "depth_sensors": depth_sensors,
            "offset": .0,
            "dH_measures": time_series._T_riv_dH_measures,
            "T_measures": time_series._T_Shaft_measures,
            "sigma_meas_P": time_series._sigma_P,
            "sigma_meas_T": time_series._sigma_T,
        }
        colonne_exp = Column.from_dict(col_dict)

        """Layer"""
        monolayer_dict = {
            "name": "sable",
            "zLow": depth_sensors[-1],
            "moinslog10K": moinslog10K,
            "n": n,
            "lambda_s": lambda_s,
            "rhos_cs": rho_cs
        }
        monolayer = Layer.from_dict(monolayer_dict)
        
        >>> analy_sol_exp.generate_RMSE_analytical(time_series, colonne_exp, monolayer)
        --- Compute Solve Transi ---
        One layer : moinslog10K = 12, n = 0.1, lambda_s = 2, rhos_cs = 4000000.0
        Done.
        array([0.00123811, 0.00315148, 0.00548253, 0.00372034])
        ```
    * **Exemple (Plot) :**
        ```python
        >>> t_fin = 1500
        >>> for i,id_sens in enumerate(analy_sol_exp._id_sensors) :
        ...     plt.plot(analy_sol_exp.analy_temp_general[id_sens,:t_fin],label="Tanaly{}".format(i+1))
        >>> plt.plot(time_series._T_Shaft[:t_fin,i],linestyle="--",label="Tmd{}".format(i+1))
        >>> plt.legend()
        >>> plt.grid()
        ```