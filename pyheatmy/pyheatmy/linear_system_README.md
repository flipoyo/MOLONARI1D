# Readme-code-1D
Ce document décrit le fonctionnement de la résolution numérique 1D des équations de charge et de température pour un aquifère stratifié, incluant un terme source/puits.

### But

Le but de ce code est de simuler l'évolution de la **charge hydraulique (H)** et de la **température (T)** le long d'un profil vertical (axe z) au sein d'un aquifère. Le modèle prend en compte la diffusion de la charge et de la chaleur, ainsi que le transport de chaleur par advection (écoulement de l'eau). Il permet également d'intégrer un terme source/puits volumique `q` pour modéliser les échanges radiaux dans notre couche.

### Modèle et zoom sur le terme q

Il faut imaginer le capteur comme planté dans le sol, mais pas parfaitement au centre de la rivière, plutôt dans un endroit quelconque. Cela permet d'éviter les confusions sur les échanges latéraux.

Pour la mise en équation, on considèrera que le capteur est planté parfaitement verticalement dans le sol. Ainsi, la charge et la température seront des fonctions uniquement de z sur le profil considéré, puisqu'on travaille avec les autres coordonées d'espaces constantes. Pour la mise en équation, on considère un cylindre de contrôle (d'axe le capteur) d'épaisseur dz sur lequel charge et température sont uniformes. 

Sur les bords de notre cylindre de contrôle, par advection diffusion il existe un flux d'eau. En nommant $q_s$ le flux d'eau total latéral par mètre de colonne on a $q_{s}dz =  \iint_{S_{lat}} \vec{q} \cdot d\vec{S}$. Cette quantité sera considérée comme uniforme sur z. Cette hypothèse est justifiée par le fait que notre capteur n'est pas très long en comparatif de la longueur totale de l'aquifère. On la traitera donc comme un terme source constant nommé $q_s$. Le terme q comprend donc l'advection et la diffusion radiales à notre capteur, il s'exprime donc à l'aide des dérivées spatiales de H selon x et y qu'on ne peut évaluer. Le fait de tout regrouper dans un seul paramètre constant q nous permet de le calculer en l'inférant dans notre MCMC.

Ce flux est directement relié à l'équation de la charge par la loi de Darcy. Pour la température, on considérera que la quantité totale d'eau entrante / sortante est à la température du cylindre de contrôle. Cette approximation se justifie par le fait que les variations radiales de température et de charge sont négligeables devant les variations verticales. Le terme à rajouter dans les équations est donc $\rho_w c_w q_s T$.

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

Les équations discrétisées (dans l'intérieur du domaine) sont :

$$S_s \frac{H_{i}^{n+1} - H_{i}^{n}}{\Delta t} = \alpha \left[ K \frac{H_{i+1}^n - 2H_{i}^n + H_{i-1}^n}{(\Delta z)^2} \right] + (1-\alpha) \left[ K \frac{H_{i+1}^{n+1} - 2H_{i}^{n+1} + H_{i-1}^{n+1}}{(\Delta z)^2} \right] + q_s$$

$$\frac{T_{i}^{n+1} - T_{i}^{n}}{\Delta t} = \alpha \left\{ \kappa_e \frac{T_{i+1}^n - 2T_{i}^n + T_{i-1}^n}{(\Delta z)^2} - \alpha_e \left(\frac{H_{i+1}^n - H_{i-1}^n}{2\Delta z}\right)\left(\frac{T_{i+1}^n - T_{i-1}^n}{2\Delta z}\right) \right\} + (1-\alpha) \left\{ \kappa_e \frac{T_{i+1}^{n+1} - 2T_{i}^{n+1} + T_{i-1}^{n+1}}{(\Delta z)^2} - \alpha_e \left(\frac{H_{i+1}^{n+1} - H_{i-1}^{n+1}}{2\Delta z}\right)\left(\frac{T_{i+1}^{n+1} - T_{i-1}^{n+1}}{2\Delta z}\right) \right\} + {\frac{\rho_w c_w}{\rho_m c_m} q_s \left((1-\alpha)T^{n+1}_i + \alpha T^{n}_i\right)}$$

### Conditions initiales

Les profils initiaux de charge et de température ($t=0$) doivent être définis sur toute la colonne verticale `z` pour initialiser la résolution. Comme nous n'avons que 5 points de mesure pour T, et une mesure de différence de charge pour H, on procédera par interpolation de Lagrange d'ordre 5 pour T, et pour H on fera une interpolation linéaire avec $H_{aq} = 0$. La charge étant définie à une constante près on peut fixer sa valeur dans l'aquifère à 0 (la charge varie peu dans l'aquifère, elle varie plus proche de la surface ou le débit d'eau varie).

$$\begin{cases}
H(z, t=0) \\
T(z, t=0)
\end{cases} \quad
\text{Calculés par interpolation sur les points de mesure initiaux.}
$$

### Conditions aux limites

Nous allons raisonner sur la charge, mais le principe est le même pour la température.

Nous imposons des conditions de **Dirichlet** (valeur imposée, nos mesures) en haut et en bas du domaine de simulation, qui peuvent varier dans le temps. De manière plus précise, ces conditions fixent les valeurs sur les points fictifs du maillage $i=-\frac{1}{2}$ et $i=n+\frac{1}{2}$.

Notre but est d'estimer $K \frac{\partial^2 H}{\partial z^2}$ au noeud 0. On ne peut pas utiliser la formule usuelle car on ne connaît pas la valeur au point -1, mais on connaît celle en $-\frac{1}{2}$. En faisant les DL, on a :
$$\begin{cases}
    H_{riv} = H_0 - H'_0 \frac{\Delta z}{2} + H''_0 \frac{\Delta z^2}{8} - O(\Delta z^3) \quad \text{(1)} \\
    \\
    H_1 = H_0 + H'_0 \Delta z + H''_0 \frac{\Delta z^2}{2} + O(\Delta z^3) \quad \text{(2)}
\end{cases}$$

Ensuite, pour éliminer le terme en $H'_0$, on combine les deux équations. En calculant $2 \times (1) + (2)$, on peut isoler $H''_0$ et on obtient :
$$H''_0 \approx \frac{1}{\Delta z^2} \left( \frac{8}{3} H_{riv} - 4 H_0 + \frac{4}{3} H_1 \right)$$

On a donc 
$$S_s \frac{H_{0}^{n+1} - H_{0}^{n}}{\Delta t} = \alpha \left[  \frac{K}{\Delta z^2} \left( \frac{8}{3} H_{riv}^n - 4 H_0^n + \frac{4}{3} H_1^n \right) \right] + (1-\alpha) \left[  \frac{K}{\Delta z^2} \left( \frac{8}{3} H_{riv}^{n+1} - 4 H_0^{n+1} + \frac{4}{3} H_1^{n+1} \right) \right] + q_s$$

C'est la formule utilisée dans le code pour évaluer la dérivée seconde sur la frontière. Pour la frontière en $n+\frac{1}{2}$ on procède de la même manière.

### Système d'équations après discrétisation

La discrétisation conduit à un système d'équations linéaires de la forme $A(\alpha) X^{n+1} = B(\alpha)X^{n} + C^{n,n+1}$, où $X$ est le vecteur des charges ou des températures à l'instant `n`.

* **Matrice A et B** : Les matrice $A$ et $B$ sont **tridiagonales** et constantes dans le temps. Leur taille est $N_z \times N_z$, où $N_z$ est le nombre de points de discrétisation sur l'axe vertical. On a $B(0)=Id$  (schéma implicite), $A(1)=Id$  (schéma explicite).

* **Vecteur C** : Le vecteur C permet d'introduire les conditions aux limites au temps n et n+1 (on fait une moyenne pondérée par $\alpha$ pour coller au schéma). Pour la charge, le terme q_s sera implémenté dans C, pour la température comme il est en préfacteur de T il sera directement implémenté dans A et B.

Pour la charge, on a $A_H(\alpha) H^{n+1} = B_H(\alpha)H^{n} + C_H^{n,n+1}$, avec :

<br>

$\mathbf{A_H(\alpha)} = 
\begin{pmatrix}
\frac{S_s}{\Delta t} + (1-\alpha)\frac{4K}{(\Delta z)^2} & -(1-\alpha)\frac{4K}{3(\Delta z)^2} & 0 & \cdots & 0 \\
-(1-\alpha)\frac{K}{(\Delta z)^2} & \frac{S_s}{\Delta t} + (1-\alpha)\frac{2K}{(\Delta z)^2} & -(1-\alpha)\frac{K}{(\Delta z)^2} & \ddots & \vdots \\
0 & \ddots & \ddots & \ddots & 0 \\
\vdots & \ddots & -(1-\alpha)\frac{K}{(\Delta z)^2} & \frac{S_s}{\Delta t} + (1-\alpha)\frac{2K}{(\Delta z)^2} & -(1-\alpha)\frac{K}{(\Delta z)^2} \\
0 & \cdots & 0 & -(1-\alpha)\frac{4K}{3(\Delta z)^2} & \frac{S_s}{\Delta t} + (1-\alpha)\frac{4K}{(\Delta z)^2}
\end{pmatrix}$

<br>

$\mathbf{B_H(\alpha)} = 
\begin{pmatrix}
\frac{S_s}{\Delta t} -\alpha \frac{4K}{(\Delta z)^2} & \alpha \frac{4K}{3(\Delta z)^2} & 0 & \cdots & 0 \\
\alpha \frac{K}{(\Delta z)^2} & \frac{S_s}{\Delta t} -\alpha \frac{2K}{(\Delta z)^2} & \alpha \frac{K}{(\Delta z)^2} & \ddots & \vdots \\
0 & \ddots & \ddots & \ddots & 0 \\
\vdots & \ddots & \alpha \frac{K}{(\Delta z)^2} & \frac{S_s}{\Delta t} -\alpha \frac{2K}{(\Delta z)^2} & \alpha \frac{K}{(\Delta z)^2} \\
0 & \cdots & 0 & \alpha \frac{4K}{3(\Delta z)^2} & \frac{S_s}{\Delta t} - \alpha \frac{4K}{(\Delta z)^2}
\end{pmatrix}$

 <br>

$\mathbf{C^{j,j+1}} =
\begin{pmatrix}
\frac{8 K}{3 (\Delta z)^2} \left[ (1-\alpha)H_{riv}^{j+1} + \alpha H_{riv}^{j} \right] + q_{s} \\
q_{s} \\
\vdots \\
q_{s} \\
\vdots \\
\frac{8 K}{3 (\Delta z)^2} \left[ (1-\alpha)H_{aq}^{j+1} + \alpha H_{aq}^{j} \right] + q_{s}
\end{pmatrix}$

<br>

### Résolution numérique

* **Résolution efficace** : Puisque le système est tridiagonal, il est résolu de manière très efficace à l'aide de l'**algorithme de Thomas** (implémenté dans la fonction `solver`, voir plus dans solver_README.md). Cet algorithme a une complexité linéaire $O(N_z)$, ce qui est beaucoup plus rapide qu'un solveur générique (comme l'élimination de Gauss).

* **Déroulement** : Pour chaque pas de temps (toutes les 15 minutes), le code :
    1.  Calcule le membre de droite ($B X^{n} + C^{n,n+1}$) qui dépend de l'état connu à l'instant `n` et des conditions aux limites. 
    2.  Construit la matrice $A$.
    3.  Appelle le `solver` pour trouver $X^{n+1}$.
    4.  Le processus est répété pour toute la durée de la simulation.