# Readme-code-1D
Ce document decrit le fonctionnement de la resolution numerique 1D des equations de charge et de temperature pour un aquifere stratifie, incluant un terme source/puits.

### But

Le but de ce code est de simuler l'evolution de la **charge hydraulique (H)** et de la **temperature (T)** le long d'un profil vertical (axe z) au sein d'un aquifere. Le modele prend en compte la diffusion de la charge et de la chaleur, ainsi que le transport de chaleur par advection (ecoulement de l'eau). Il permet egalement d'integrer un terme source/puits volumique `q` pour modeliser les echanges radiaux dans notre couche.

<br>

## Modele et zoom sur le terme q

Il faut imaginer le capteur comme plante dans le sol, mais pas parfaitement au centre de la riviere, plutot dans un endroit quelconque. Cela permet d'eviter les confusions sur les echanges lateraux.

Pour la mise en equation, on considerera que le capteur est plante parfaitement verticalement dans le sol. Ainsi, la charge et la temperature seront des fonctions uniquement de z sur le profil considere, puisqu'on travaille avec les autres coordonees d'espaces constantes. Pour la mise en equation, on considere un cylindre de controle (d'axe le capteur) d'epaisseur dz sur lequel charge et temperature sont uniformes. 

Sur les bords de notre cylindre de controle, par advection diffusion il existe un flux d'eau. En nommant $q_s$ le flux d'eau total lateral par metre de colonne on a $q_{s}dz =  \iint_{S_{lat}} \vec{q} \cdot d\vec{S}$. Cette quantite sera consideree comme uniforme sur z. Cette hypothese est justifiee par le fait que notre capteur n'est pas tres long en comparatif de la longueur totale de l'aquifere. On la traitera donc comme un terme source constant nomme $q_s$. Le terme $q_s$ comprend donc l'advection et la diffusion radiales a notre capteur, il s'exprime donc a l'aide des derivees spatiales de H selon x et y qu'on ne peut evaluer faute de mesures. Le fait de tout regrouper dans un seul parametre constant $q_s$ nous permet de le calculer en l'inferant dans notre MCMC.

L'equation de la charge est obtenue par un bilan de masse couple a la loi de Darcy. Pour tenir en compte de $q_s$ dans l'equation il suffit donc d'ajouter un flux. L'equation de temperature est elle obtenue par un bilan d'energie. On cherche donc a connaitre la quantite d'energie apportee par notre flux. Pour simplifier, on considerera que la quantite totale d'eau entrante / sortante est a la temperature du cylindre de controle. Cette approximation se justifie par le fait que les variations radiales de temperature et de charge sont negligeables devant les variations verticales. Le terme a rajouter dans le bilan d'energie est donc $\rho_w c_w q_s T$.

On utilise ce subterfuge de calcul car notre capteur ne nous donne que des informations selon l'axe z. On ne peut donc resoudre notre equation que sur ce profil d'espace, et avec les informations disponibles.

<br>

## Equations

Les equations traitees sont les suivantes :

1.  **Equation de charge hydraulique (H), obtenue par bilan de masse couple a la loi de Darcy :**

$$S_s \frac{\partial H}{\partial t} = K \Delta H$$

2.  **Equation de temperature (T), obtenue par bilan d'energie :**
$$\frac{\partial T}{\partial t} = \kappa_e \Delta T + \alpha_e \nabla H \cdot \nabla T$$

En 1D en incluant le terme source, on a donc :

1.  **Equation de charge hydraulique (H) :**
    $$S_s \frac{\partial H}{\partial t} = K \frac{\partial^2 H}{\partial z^2}  + q_s$$
2.  **Equation de temperature (T) :**
    $$\frac{\partial T}{\partial t} = \underbrace{\kappa_e \frac{\partial^2 T}{\partial z^2}}_{\text{Diffusion}} + \underbrace{\alpha_e \frac{\partial H}{\partial z} \frac{\partial T}{\partial z}}_{\text{Advection}} + \underbrace{\frac{\rho_w c_w}{\rho_m c_m} q_s T}_{\text{Source}}$$

<br>

## Discretisation de l'equation a l'interieur du domaine

Pour resoudre numeriquement ces equations, nous utilisons un **$\theta$-schema** pondere par un parametre $\alpha$.
* $\alpha = 0$ : Schema totalement **implicite** (inconditionnellement stable).
* $\alpha = 0.5$ : Schema de Crank-Nicolson classique.
* $\alpha = 1$ : Schema totalement **explicite** (conditionnellement stable).

Les variables sont notees $U^{n}_{i}$, où `n` est l'indice temporel et `i` l'indice spatial sur l'axe vertical `z`.

Les equations discretisees (dans l'interieur du domaine) sont :

$$S_s \frac{H_{i}^{n+1} - H_{i}^{n}}{\Delta t} = \alpha \left[ K \frac{H_{i+1}^n - 2H_{i}^n + H_{i-1}^n}{(\Delta z)^2} \right] + (1-\alpha) \left[ K \frac{H_{i+1}^{n+1} - 2H_{i}^{n+1} + H_{i-1}^{n+1}}{(\Delta z)^2} \right] + q_s$$

$$\frac{T_{i}^{n+1} - T_{i}^{n}}{\Delta t} = \alpha \left\{ \kappa_e \frac{T_{i+1}^n - 2T_{i}^n + T_{i-1}^n}{(\Delta z)^2} - \alpha_e \left(\frac{H_{i+1}^n - H_{i-1}^n}{2\Delta z}\right)\left(\frac{T_{i+1}^n - T_{i-1}^n}{2\Delta z}\right) \right\} + (1-\alpha) \left\{ \kappa_e \frac{T_{i+1}^{n+1} - 2T_{i}^{n+1} + T_{i-1}^{n+1}}{(\Delta z)^2} - \alpha_e \left(\frac{H_{i+1}^{n+1} - H_{i-1}^{n+1}}{2\Delta z}\right)\left(\frac{T_{i+1}^{n+1} - T_{i-1}^{n+1}}{2\Delta z}\right) \right\} + {\frac{\rho_w c_w}{\rho_m c_m} q_s \left((1-\alpha)T^{n+1}_i + \alpha T^{n}_i\right)}$$

<br>

## Conditions aux limites

Nous allons raisonner sur la charge, mais le principe est le même pour la temperature.

Nous imposons des conditions de **Dirichlet** (valeur imposee, nos mesures) en haut et en bas du domaine de simulation, qui peuvent varier dans le temps. De maniere plus precise, ces conditions fixent les valeurs sur les points fictifs du maillage $i=-\frac{1}{2}$ et $i=n+\frac{1}{2}$.

Notre but est d'estimer $K \frac{\partial^2 H}{\partial z^2}$ au noeud 0. On ne peut pas utiliser la formule usuelle car on ne connaît pas la valeur au point -1, mais on connaît celle en $-\frac{1}{2}$. En faisant les DL, on a :
$$\begin{cases}
    H_{riv} = H_0 - H'_0 \frac{\Delta z}{2} + H''_0 \frac{\Delta z^2}{8} - O(\Delta z^3) \quad \text{(1)} \\
    \\
    H_1 = H_0 + H'_0 \Delta z + H''_0 \frac{\Delta z^2}{2} + O(\Delta z^3) \quad \text{(2)}
\end{cases}$$

Ensuite, pour eliminer le terme en $H'_0$, on combine les deux equations. En calculant $2 \times (1) + (2)$, on peut isoler $H''_0$ et on obtient :
$$H''_0 \approx \frac{1}{\Delta z^2} \left( \frac{8}{3} H_{riv} - 4 H_0 + \frac{4}{3} H_1 \right)$$

On a donc 
$$S_s \frac{H_{0}^{n+1} - H_{0}^{n}}{\Delta t} = \alpha \left[  \frac{K}{\Delta z^2} \left( \frac{8}{3} H_{riv}^n - 4 H_0^n + \frac{4}{3} H_1^n \right) \right] + (1-\alpha) \left[  \frac{K}{\Delta z^2} \left( \frac{8}{3} H_{riv}^{n+1} - 4 H_0^{n+1} + \frac{4}{3} H_1^{n+1} \right) \right] + q_s$$

C'est la formule utilisee dans le code pour evaluer la derivee seconde sur la frontiere. Pour la frontiere en $n+\frac{1}{2}$ on procede de la même maniere.

<br>

## Conditions initiales

Les profils initiaux de charge et de temperature ($t=0$) doivent être definis sur toute la colonne verticale `z` pour initialiser la resolution. Comme nous n'avons que 5 points de mesure pour T, et une mesure de difference de charge pour H, on procedera par interpolation de Lagrange d'ordre 5 pour T, et pour H on fera une interpolation lineaire avec $H_{aq} = 0$. La charge etant definie a une constante pres on peut fixer sa valeur dans l'aquifere a 0 (la charge varie peu dans l'aquifere, elle varie plus proche de la surface ou le debit d'eau varie).

$$\begin{cases}
H(z, t=0) \\
T(z, t=0)
\end{cases} \quad
\text{Calcules par interpolation sur les points de mesure initiaux.}
$$

<br>

## Systeme d'equations apres discretisation

La discretisation conduit a un systeme d'equations lineaires de la forme $A(\alpha) X^{n+1} = B(\alpha)X^{n} + C^{n,n+1}$, où $X$ est le vecteur des charges ou des temperatures a l'instant `n`.

* **Matrice A et B** : Les matrice $A$ et $B$ sont **tridiagonales** et constantes dans le temps. Leur taille est $N_z \times N_z$, où $N_z$ est le nombre de points de discretisation sur l'axe vertical. On a $B(0)=Id$  (schema implicite), $A(1)=Id$  (schema explicite).

* **Vecteur C** : Le vecteur C permet d'introduire les conditions aux limites au temps n et n+1 (on fait une moyenne ponderee par $\alpha$ pour coller au schema). Pour la charge, le terme q_s sera implemente dans C, pour la temperature comme il est en prefacteur de T il sera directement implemente dans A et B.

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

## Resolution numerique

* **Resolution efficace** : Puisque le systeme est tridiagonal, il est resolu de maniere tres efficace a l'aide de l'**algorithme de Thomas** (implemente dans la fonction `solver`, voir plus dans solver_README.md). Cet algorithme a une complexite lineaire $O(N_z)$, ce qui est beaucoup plus rapide qu'un solveur generique (comme l'elimination de Gauss).

* **Deroulement** : Pour chaque pas de temps (toutes les 15 minutes), le code :
    1.  Calcule le membre de droite ($B X^{n} + C^{n,n+1}$) qui depend de l'etat connu a l'instant `n` et des conditions aux limites. 
    2.  Construit la matrice $A$.
    3.  Appelle le `solver` pour trouver $X^{n+1}$.
    4.  Le processus est repete pour toute la duree de la simulation.