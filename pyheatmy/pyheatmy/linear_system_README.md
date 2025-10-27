# Readme-code-1D
Ce document décrit le fonctionnement de la résolution numérique 1D des équations de charge et de température pour un aquifère stratifié, incluant un terme source/puits.

### But

Le but de ce code est de simuler l'évolution de la **charge hydraulique (H)** et de la **température (T)** le long d'un profil vertical (axe z) au sein d'un aquifère. Le modèle prend en compte la diffusion de la charge et de la chaleur, ainsi que le transport de chaleur par advection (écoulement de l'eau). Il permet également d'intégrer un terme source/puits volumique `q` pour modéliser les échanges radiaux dans notre couche.

### Modèle et zoom sur le terme q

Il faut imaginer le capteur comme planté dans le sol, mais pas parfaitement au centre de la rivière, plutôt dans un endroit quelconque. Cela permet d'éviter les confusions sur les échanges latéraux.

Pour la mise en équation, on considèrera que le capteur est planté parfaitement verticalement dans le sol. Ainsi, la charge et la température seront des fonctions uniquement de z sur le profil considéré, puisqu'on travaille avec les autres coordonées d'espaces constantes. Pour la mise en équation, on considère un cylindre de contrôle (d'axe le capteur) d'épaisseur dz sur lequel charge et température sont uniformes. 

Sur les bords de notre cylindre de contrôle, par advection diffusion il existe un flux d'eau. En nommant $q_s$ le flux d'eau total latéral par mètre de colonne on a $q_{s}dz =  \iint_{S_{lat}} \vec{q} \cdot d\vec{S}$. Cette quantité sera considérée comme uniforme sur z. Cette hypothèse est justifiée par le fait que notre capteur n'est pas très long en comparatif de la longueur totale de l'aquifère. On la traitera donc comme un terme source constant nommé $q_s$. Le terme q comprend donc l'advection et la diffusion radiales à notre capteur, il s'exprime donc à l'aide des dérivées spatiales de H selon x et y qu'on ne peut évaluer. Le fait de tout regrouper dans un seul paramètre constant q nous permet de le calculer en l'inférant dans notre MCMC.

Ce flux est directement relié à l'équation de la charge par la loi de Darcy. Pour la température, on considérera que la quantité totale d'eau entrante / sortante est à la température du cylindre de contrôle. Cette approximation se justifie par le fait que les variations radiales de température et de charge sont négligeables devant les variations verticales. Le terme à rajouter dans les équations est donc $\rho_e c_e q_s T$.

On utilise ce subterfuge de calcul car notre capteur ne nous donne que des informations selon l'axe z. On ne peut donc résoudre notre équation que sur ce profil d'espace, et avec les informations disponibles.

### Équations

Les équations traitées sont les suivantes :

1.  **Équation de charge hydraulique (H) :**
$$S_s \frac{\partial H}{\partial t} = K \Delta H$$ 

2.  **Équation de température (T) :**
$$\frac{\partial T}{\partial t} = \kappa_e \Delta T + \alpha_e \nabla H \cdot \nabla T$$

En 1D en incluant le terme source, on a donc :

1.  **Équation de charge hydraulique (H) :**
    $$S_s \frac{\partial H}{\partial t} = K \frac{\partial^2 H}{\partial z^2}  + q_s$$
2.  **Équation de température (T) :**
    $$\frac{\partial T}{\partial t} = \underbrace{\kappa_e \frac{\partial^2 T}{\partial z^2}}_{\text{Diffusion}} + \underbrace{\alpha_e \frac{\partial H}{\partial z} \frac{\partial T}{\partial z}}_{\text{Advection}} + \underbrace{\frac{\rho_w c_w}{\rho_m c_m} q_s T}_{\text{Source}}$$

### Discrétisation

Pour résoudre numériquement ces équations, nous utilisons un **$\theta$-schema** pondéré par un paramètre $\alpha$.
* $\alpha = 0$ : Schéma totalement **implicite** (inconditionnellement stable).
* $\alpha = 0.5$ : Schéma de Crank-Nicolson classique.
* $\alpha = 1$ : Schéma totalement **explicite** (conditionnellement stable).

Les variables sont notées $U^{n}_{i}$, où `n` est l'indice temporel et `i` l'indice spatial sur l'axe vertical `z`.

Les équations discrétisées sont :

$$S_s \frac{H_{i}^{n+1} - H_{i}^{n}}{\Delta t} = \alpha \left[ K \frac{H_{i+1}^n - 2H_{i}^n + H_{i-1}^n}{(\Delta z)^2} \right] + (1-\alpha) \left[ K \frac{H_{i+1}^{n+1} - 2H_{i}^{n+1} + H_{i-1}^{n+1}}{(\Delta z)^2} \right] + q_s$$

$$\frac{T_{i}^{n+1} - T_{i}^{n}}{\Delta t} = \alpha \left\{ \kappa_e \frac{T_{i+1}^n - 2T_{i}^n + T_{i-1}^n}{(\Delta z)^2} - \alpha_e \left(\frac{H_{i+1}^n - H_{i-1}^n}{2\Delta z}\right)\left(\frac{T_{i+1}^n - T_{i-1}^n}{2\Delta z}\right) \right\} + (1-\alpha) \left\{ \kappa_e \frac{T_{i+1}^{n+1} - 2T_{i}^{n+1} + T_{i-1}^{n+1}}{(\Delta z)^2} - \alpha_e \left(\frac{H_{i+1}^{n+1} - H_{i-1}^{n+1}}{2\Delta z}\right)\left(\frac{T_{i+1}^{n+1} - T_{i-1}^{n+1}}{2\Delta z}\right) \right\} + {\frac{\rho_w c_w}{\rho_m c_m} q_s \left((1-\alpha)T^{n+1}_i + \alpha T^{n}_i\right)}$$

### Conditions initiales

Les profils initiaux de charge et de température ($t=0$) doivent être définis sur toute la colonne verticale `z` pour initialiser la résolution. Comme nous n'avons que 5 points de mesure pour T, et une mesure de différence de charge pour H, on procédera par interpolation de Lagrange d'ordre 5 pour T, et pour H on fera une interpolation linéaire avec $H_{aq} = 0$. 

$$\begin{cases}
H(z, t=0) \\
T(z, t=0)
\end{cases} \quad
\text{Calculés par interpolation sur les points de mesure initiaux.}
$$

### Conditions aux limites

Nous imposons des conditions de **Dirichlet** (valeur imposée) en haut et en bas du domaine de simulation, qui peuvent varier dans le temps :

$$\text{Limites haute et basse} \quad \begin{cases} H(z=0, t) = H_{riv}(t)-H_{aq}(t) \\ H(z=h, t) = 0 \end{cases} \quad \text{et} \quad \begin{cases} T(z=0, t) = T_{riv}(t) \\ T(z=h, t) = T_{aq}(t) \end{cases}$$

### Traitement numérique

La discrétisation conduit à un système d'équations linéaires de la forme $A(\alpha) X^{n+1} = B(\alpha)X^{n} + C^{n,n+1}$, où $X$ est le vecteur des charges ou des températures à l'instant `n`.

* **Matrice A et B** : Les matrice $A$ et $B$ sont **tridiagonales** et constantes dans le temps. Leur taille est $N_z \times N_z$, où $N_z$ est le nombre de points de discrétisation sur l'axe vertical. On a $B(0)=Id$  (schéma implicite), $A(1)=Id$  (schéma implicite), et $A(0.5) = B(0.5)$.

* **Vecteur C** : Le vecteur C permet d'introduire les conditions aux limites au temps n et n+1 (on fait une moyenne pondérée par $\alpha$ pour coller au schéma)

* **Résolution efficace** : Puisque le système est tridiagonal, il est résolu de manière très efficace à l'aide de l'**algorithme de Thomas** (implémenté dans la fonction `solver`). Cet algorithme a une complexité linéaire $O(N_z)$, ce qui est beaucoup plus rapide qu'un solveur générique (comme l'élimination de Gauss).

* **Déroulement** : Pour chaque pas de temps (toutes les 15 minutes), le code :
    1.  Calcule le membre de droite ($B X^{n} + C^{n+1}$) qui dépend de l'état connu à l'instant `n` et des conditions aux limites. 
    2.  Assemble les diagonales de la matrice $A$ de l'état `n+1`.
    3.  Appelle le `solver` pour trouver $X^{n+1}$.
    4.  Le processus est répété pour toute la durée de la simulation.
Ce document décrit le fonctionnement de la résolution numérique 1D des équations de charge et de température pour un aquifère stratifié, incluant un terme source/puits.