# Readme - Algorithme MCMC
_Derniere mise a jour : 2025-11-05_

Ce document decrit le fonctionnement de l'algorithme MCMC (Monte Carlo - Markov Chains) implemente dans `core.py` ainsi que la gestion de la classe `Prior` dans `params.py`.


## But

Le but de cet algorithme n'est pas de resoudre les equations physiques, mais d'**estimer les parametres physiques** (permeabilite intrinseque, porosite, conductivite thermique, capacite thermique volumique et desormais le terme de source laterale d'eau) de l'aquifere qui correspondent le mieux aux donnees de temperature et de charge observees.
Pour ce faire, on determine la **distribution de probabilite a posteriori** de ces parametres, c'est-a-dire l'ensemble des valeurs de parametres qui sont plausibles compte tenu de nos mesures et de notre modele physique.


## Modele statistique (Bayesien)

Nous cherchons a determiner la distribution a posteriori $\pi(Y|Z)$, ou $\pi(Y | Z)$, ou $Y$ represente l'ensemble de nos parametres inconnus ("State Space") et $Z$ represente nos donnes de mesures ("Observations")
D'apres le theoreme de Bayes : $$\pi(Y|Z) \propto f(Z|Y) \times f(Y)$$

- $f(Y)$ est la **distribution a priori (Prior)** : C'est notre connaissance initiale sur les parametres $Y$ avant de voir les donnees $Z$. Dans le code cela est gere par la classe `Prior` (par exemple, `Prior_IntrinK`, `Prior_n`, etc.) qui definit une plage de valeurs possibles.
- $f(Z|Y)$ est la **fonction de vraissemblance (Likelihood)** : Elle mesure la probabilite d'observer nos donnees $Z$ si les parametres etaient $Y$. Dans notre cas, elle quantifie l'ecart (l'erreur) entre les temperatures simulees par le modele $F(Y)$ et les temperatures reellement mesurees $Z$.


## Fonction "Energie" (Negative Log-Posterior)

L'algorithme MCMC n'a pas besoin de calculer la distribution $\pi(Y|Z)$ directement, mais seulement une fonction qui lui est proportionnelle. En pratique on travaille avec le **logarithme negatif** de cette distribution pour des raisons de stabilite numerique.
On appelle cette fonction "Energie" $E(Y)$. L'objectif du MCMC n'est donc plus de "maximiser la probabilite" mais "minimiser **l'energie"**.
En plus des parametres physiques, on ajoute le parametre $\sigma^2$, la variance de l'erreur entre les donnees et la realite, qui caracterise le **"niveau de confiance"** des mesures. D'apres le theoreme de Bayes, on a donc $\pi( Y | Z , \sigma ^ 2 ) \propto f (Z | Y , \sigma^2) \times f (Y) \times f (Y\sigma^2) $.
En passant au log-negatif on obtient la forme suivante pour l'energie : $E(Y, \sigma^2) \approx -\log(f(Z | Y, \sigma^2)) - \log(f(Y)) - \log(f(\sigma^2))$
La fonction `compute_energy` dans `core.py` permet de calculer cette energie en supposant des erreurs de mesure  gaussiennes: $$E(Y, \sigma^2) = \underbrace{ \left( N \log(\sigma^2) + \frac{\|Z - F(Y)\|^2}{2\sigma^2} \right) }_{\substack{ (= -\log(f(Z | Y, \sigma^2))) \\ \text{En supposant les erreurs gaussiennes}}} - \log(f(\sigma^2))$$
Ou : 

- $Z$ sont les temperatures mesurees (`temp_ref`).
- $F(Y)$ sont les temperatures simulees (`temp_simul`) en utilisant les parametres $Y$ et le modele physique $F$
- $\|Z - F(Y)\|^2$ est la somme des carres des ecarts (le `norm2` dans le script)
- $\sigma^2$ est la variance de l'erreur de mesure.
- $f(\sigma^2)$ est la distribution a priori sur cette variance (`sigma2_distrib`).
- $N$ est le nombre de points de donnees (`size(temp_ref)`)

Le terme $-log (f(Y))$ a ete neglige car il est en pratique constant, puisque les distributions a priori des parametres sont uniformes. Comme on s'interesse a des differences d'energie, cela ne fait pas la moindre difference.

Un jeu de parametres $Y$ qui produit une simulation proche des mesures ($F(Y)=Z$) aura une **faible energie** et sera donc consideree comme **plus probable**.

## Critere d'Acceptation (Metropolis)

L'algorithme explore l'espace des parametres en proposant un nouvel ensemble de parametres $Y_{prop}$ a partir d'un ensemble precedent $Y_{prev}$.

Pour decider s'il faut accepter cette proposition, on calcule un **ratio d'acceptation**. Pour un algorithme de type "Symmetric Random Walk" (utilise dans le script), le critere de Metropolis-Hastings se simplifie. La probabilite d'accepter est : $$P_{accept} = \min\left(1, \exp(E(Y_{prev}) - E(Y_{prop}))\right)$$
- Si l'energie **diminue** ($E_{prop}<E_{prev}$), la proposition est **meilleure**. Le ratio est $>1$, et la proposition est **toujours acceptee**.
- Si l'energie **augmente** ($E_{prop}>E_{prev}$), la proposition est **moins bonne**. Cependant, elle est **parfois acceptee** avec une probabilite $\exp(E(Y_{prev}) - E(Y_{prop}))$ (dont le logarithme est calcule dans le code : `log_ratio_accept = Energy[j] - Energy_Proposal` )

Cette acceptation stochastique des "mauvais" pas permet a l'algorithme d'eviter de rester bloque dans un minimum local pour explorer l'ensemble de la distribution.


## Algorithmes implementes

Le code `compute_mcmc` implemente deux variantes de l'algorithme MCMC, en fonction du nombre de chaines utilisees (`nb_chain`).

### **Premier cas** : Chaine Unique (`nb_chain = 1`) - Random Walk Metropolis (RWM)

C'est l'**aglorithme** MCMC le plus simple, qui correspond au **"Symmetric increments random-walk sampler (SIMH)"** decrit dans le cours.
1. **Initialisation** : L'algorithme teste `nitmaxburning` jeux de parametres initiaux (tires des priors) et garde le meilleur (celui qui minimise l'energie) comme point de depart.
2. **Iteration** (`nb_iter` etapes) : 
    - **Proposition** : Un nouveau jeu de parametres $Y_{prop}$ est cree en perturbant aleatoirement le jeu precedent $Y_{prev}$ (via `self.perturb_params()`, grâce au parametre `user_sigma`). C'est donc une marche aleatoire (Random Walk).
    - **Evaluation** : Le modele physique (`compute_solve_transi`) est lance avec $Y_{prop}$ pour calculer $F(Y_{prop})$ puis l'energie $E_{prop}$
    - **Decision** : La proposition est acceptee ou rejetee selon le critere de Metropolis. 
    - **Stockage** : L'etat (accepte ou non) est stocke dans `self._states`.

### **Second cas** : Chaines Multiples (`nb_chain > 1`) - DREAM

Il s'agit d'un algorithme MCMC plus avance et efficace. Il appartient a la famille des **MCMC adaptatifs** mentionnes dans le cours.
1. Phase de Burn-in (Prechauffage) :
 - Les `nb_chain` chaines sont lancees en parallele.
 - **Proposition** : Au lieu d'une simple perturbation aleatoire, les propositions sont generees en utilisant l'**evolution differentielle**. Une nouvelle proposition pour la chaine `j` est creee en faisant la difference entre les etats d'autres chaines (gere par `perturbation_DREAM`).
 - **Adaptation** : L'algorithme est adaptatif : il apprend la forme de la distribution et ajuste ses strategies de proposition (vecteur `pcr`) pendant le burn-in.
 - **Convergence** : La phase de burn-in s'arrête lorsque les chaines ont converge vers la distribution a posteriori. Cette convergence est verifiee a l'aide du **critere de Gelman-Rubin** (implemente dans`Gelman_Rubin.py`).
2. Phase MCMC Principale
 - Une fois la convergence atteinte, l'algorithme continue de tourner pour `nb_iter` etapes.
 - Il continue d'utiliser l'algorithme DREAM pour generer des propositions.
 - Tous les etats acceptes de toutes les chaines sont stockes dans `self._states` pour construire les distributions finales.

 Dans les deux cas, pour s'assurer que la MCMC ne sorte jamais de l'intervalle a priori, les bords sont geres par **modulo**. Si un un saut "sort" de l'intervalle, il "re-entre" par l'autre extremite. Cette approche, comparee a l'approche par rebonds, permet de mieux explorer de l'espace.


## Gestion des Parametres Fixes

L'implementation de `perturbation_DREAM` prend en compte un masque `is_param_fixed`. Si un parametre est marque comme "fixe" dans ses priors :
- L'algorithme MCMC ne le perturbera pas
- Il ne sera pas utilise dans le calcul de l'evolution differentielle

Cela permet a l'utilisateur de "geler" un ou plusieurs parametres a une valeur connue et de n'executer l'inference MCMC que sur les parametres restes "libres". Cette fonctionnalite a ete implementee afin d'accelerer l'optimisation si les methodes frequentielles permettent de determiner les valeurs de certains parametres avant l'optimisation.

## Resultats et Sorties

A la fin de l'execution de `compute_mcmc`, les resultats suivant sont disponibles :
- `self._states` : La liste complete de tous les etats (jeux de parametres $Y$) visites par la ou les chaines apres le burn-in.
- `get_best_params()` : Renvoie le jeu de parametres $Y$ qui a produit la **plus faible energie**. C'est l'estimateur du **MAP** (maximum a pesteriori, mentionne dans le cours), qui correspond a la valeur la plus probable de $Y$.
- `plot_all_param_pdf()` : Genere les histogrammes de `self._states`. Chaque histogramme represente la **distribution a posteriori** $\pi(Y_i|Z)$ d'un parametre $Y_i$.
- `self._quantiles_temperatures` et `self._quantiles_flows` : Calculent les quantiles (par ex. 5%, 50%, 95%) sur les **sorties du modele** (temperatures $F(Y)$ et vitesse de Darcy). Cela permet de visualiser l'incertitude du modele, un avantage majeur de l'approche bayesienne.

## Gestion des Priors (`params.py`)

Un composant essentiel du modele MCMC est la maniere dont les **priors** (distributions a priori) sont definis et geres, ce qui est fait a l'aide de la classe `Prior` dans `params.py`.

L'implementation actuelle permet de transformer l'**espace de recherche** pour rendre l'exploration de chaque parametre plus efficace.

### Le Probleme : Explorer Plusieurs Ordres de Grandeur

L'algorithme MCMC explore l'espace en creant de nouvelles propositions basees sur les etats precedents.
 - Si un parametre (comme $K$) varie sur plusieurs ordres de grandeur dans son **espace physique** (ex: de `1e-15` a `1e-12`), cet espace n'est pas propice a la MCMC. La quasi-totalite du volume de l'intervalle est concentree pres de la borne superieure.
 - L'algorithme MCMC serait incapable d'explorer l'integralite de l'intervalle, que la variante RMW ou DREAM soit utilisee.

 ### La solution : Un "Traducteur Geometrique" Integre a la classe `Prior`

 La classe `Prior` agit comme un traducteur qui convertit l'**espace physique** (`user_range`) en un **espace de travail MCMC** (`mcmc_range`).

1. **Transformation automatique d'echelle**
    
Lors de son initialisation, le `Prior` analyse le `user_range` (intervalle physique fourni par l'utilisateur) et choisit automatiquement la meilleure transformation :
- `scale = 'linear'`
    - **Cas** : Pour les parametres simples (ex: porosite `n` de `0.01` a `0.3`) ou les intervalles larges traversant zero (ex: `(-5,5)`)
    - **Transformation** : L'espace MCMC est le même que l'espace physique.
    - **Resultat** : `user_range = (0.1, 0.3)` $\rightarrow$ ``mcmc_range = (0.1, 0.3)``.
- ``scale = 'log'``
    - **Cas** : Pour les parametres strictements positifs couvrant plusieurs ordres de grandeur. Le seuil de declenchement est ``upper_bound / lower_bound > LOG_SCALE_THRESHOLD`` (où ``LOG_SCALE_THRESHOLD`` est $\sqrt{10\times100}$ dans ``config.py``)
    - **Transformation** : La methode `physical_to_mcmc` applique `np.log10()`.
    - **Resultat** : `user_range = (1e-15, 1e-12)` $\rightarrow$ `mcmc_range = (-15, -12)`
    - **Benefice** : la MCMC explore l'exposant de maniere uniforme, ce qui est physiquement beaucoup plus pertinent.
- `scale = 'symlog'` (Logarithme symetrique)
    - **Cas** : Pour les parametres qui traversent zero, tout en couvrant plusieurs ordres de grandeur (ex: la source `q_s` sur `(-1e-5,1e-5)`). Se declenche si l'intervalle traverse zero et que sa magnitude est faible (`<SYMLOG_MAGNITUDE_THRESHOLD`, fixe a `1e-1` dans  `config.py`).
    - **Transformation** : Comme `log10(0)` est indefini, la classe `Prior` definit un seuil lineaire (`lintresh`) au voisinage de zero.
        - Dans l'intervalle `[-lintresh, +lintresh]`, la transformation est lineaire.
        - A l'exterieur, la transformation est logarithmique (`log10(abs(val) / lintresh)`).
    - **Benefice** : Permet a l'algorithme d'explorer efficacement les tres petites valeurs autour de zero *et* les ordres de grandeur superieurs.

Dans le cas ou l'algorithme **RMW** est utilise, les valeurs `user_sigma` fournies par l'utilisateur sont adaptees au nouvel espace par `_translate_sigma()`