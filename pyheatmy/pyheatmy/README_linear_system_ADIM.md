# Note sur adimensionnement des équations

# Problème général

On cherche à solutionner le couple d'équations suivantes:

$$
\left\{\begin{array}{lll}
S_s \partial_t H & = & \partial_z (K \partial_z H) + q_s \\
\rho_m c_m \partial_t T & = & \rho_w c_w q \partial_z T + \lambda_m \partial_z^2 T + q_s
\end{array} \right.
$$

avec :

- $q = K \partial_z H$ (Flux de Darcy)
- $K = \frac{k\rho_w g}{\mu_w} = \frac{k g}{\nu_w}$ (Conductivité hydraulique)
- $q_s = \text{flux latéral d'eau } (s^{-1})$

L'adimensionnement de ces l'équation est utile pour simplifier la résolution si certains termes sont dominants. Ce n'est pas le cas ici : les termes peuvent tous être importants, cela dépend du régime.
En outre, en adimensionnant correctement l'équation, tout les paramètres adimensionnés sont de l'ordre de l'unité. Cela limite donc les erreurs de calcul. Cela augmente aussi l'efficacité de calcul.

On notera que l'axe z est dirigé vers le bas, d'où la définition de ${\Delta T}$ et ${\Delta H}$ par la suite.

## Adimensionnement et premières déductions

On pose les changements de variables suivants :

$$
\tilde{z}= \frac{z}{L_0} \quad \text{;} \quad \tilde{t}= \frac{t}{P} \quad \text{;} \quad \tilde{H} = \frac{H - H_{riv}}{H_{nap}-H_{riv}} =  \frac{H - H_{riv}}{\Delta H} \quad \text{;} \quad \tilde{\theta} = \frac{\theta - T_{riv}}{T_{nap}-T_{riv}} =  \frac{\theta - T_{riv}}{\Delta T}
$$

Ici $L_0$ est la prfondeur de la colonne de sol étudiée, $P$ est la période caractéristique de variations de la température.

On exprime les équations avec les nouvelles variables pour obtenir les équations adimensionnées. La perméabilité $K$, l'emmagasinement spécifiques $S_{s}$ et les flux latéraux $q_s$ et $q_s$ sont pris constants à l'intérieur d'une couche, domaine de validité de ces équation :

$$
\left\{\begin{array}{rll}
\dfrac{S_s \Delta H }{P} \, \, \partial_{\tilde{t}} \tilde{H} & = & \dfrac{K \Delta H}{L_0^2}  \, \, \partial_{\tilde{z}}^2 \tilde{H} \, \, + q_s \\
\dfrac{\rho_m c_m \Delta T}{P}  \, \, \partial_{\tilde{t}} \tilde{\theta}  & = & \dfrac{\rho_w c_w K \Delta H \Delta T}{L_0^2}  \, \, \partial_{\tilde{z}} \tilde{H}  \, \, \partial_{\tilde{z}} \tilde{\theta} + \dfrac{\lambda_m \Delta T}{L_0^2}  \, \, \partial_{\tilde{z}}^2  \tilde{\theta} + \rho_w c_w q_s \Delta T
\end{array} \right.
$$

On regroupe ensuite les paramètres pour obtenir les composantes principales du système, en divisant la première ligne par $\frac{K \Delta H}{L_0^2}$ et la seconde par $\frac{\lambda_m \Delta T}{L_0^2}$:

$$
\left\{\begin{array}{rll}
\overbrace{\dfrac{S_s L_0^2}{P K }}^{\large{\gamma}}  \, \, \partial_{\tilde{t}} \tilde{H} & = & \partial_{\tilde{z}}^2 \tilde{H} \, \,
+ \overbrace{\dfrac{L_0^2 q_s}{K \Delta H}}^{\large{\zeta}} \\[15pt]
\underbrace{\dfrac{\rho_m c_m L_0^2}{P \lambda_m}}_{\large{\beta}}  \, \, \partial_{\tilde{t}} \tilde{\theta}  & = & \underbrace{\dfrac{\rho_w c_w K \Delta H}{\lambda_m}}_{\large{\kappa = \text{Pe}}}  \, \, \partial_{\tilde{z}} \tilde{H} \, \, \partial_{\tilde{z}} \tilde{\theta} + \partial_{\tilde{z}}^2  \tilde{\theta} + \underbrace{\dfrac{\rho_w c_w q_s L_0^2}{\lambda_m}}_{\large{\phi}}
\end{array} \right.
$$

On considère donc le système adimensionné suivant:

$$
\left\{\begin{array}{rll}
\gamma \times \partial_{\tilde{t}} \tilde{H}      & = & \, \zeta & + & \partial_{\tilde{z}}^2 \tilde{H} \\
\beta  \times \, \, \partial_{\tilde{t}} \tilde{\theta} & = & \kappa \times \partial_{\tilde{z}} \tilde{H} \times \partial_{\tilde{z}} \tilde{\theta} & + & \partial_{\tilde{z}}^2 \tilde{\theta} + \phi
\end{array} \right.
$$

avec les 5 paramètres (sans dimensions) calculés dans la couche :

$$
\kappa = \text{Pe} = \frac{\rho_w^2 c_w k g \Delta H}{\mu_w \lambda_m} \quad ; \quad \beta = \frac{\rho_m c_m L_0^2}{\lambda_m P }  \quad ; \quad  \gamma = \frac{\mu_w L_0^2 S_s}{k \rho_w g P} \quad ; \quad \zeta = \dfrac{L_0^2 q_s}{K \Delta H} \quad ; \quad \phi = \frac{\rho_w c_w q_s L_0^2}{\lambda_m}
$$

_(Note : La formule de $\kappa$ (Péclet) est correcte en substituant $K = \frac{k\rho_w g}{\mu_w}$ dans $\frac{\rho_w c_w K \Delta H}{\lambda_m}$)_

IMPORTANT: Cette analyse montre que les profils de température et de charge dépendant uniquement de ces cinq paramètres $\kappa$ (ou Pe), $\beta$, $\gamma$, $\zeta$ et $\phi$. Il est donc possible (sauf cas particulier) de déterminer ces cinq paramètres si on nous donne un profil.

Le problème initial contient lui plus de paramètres: $n$, $k$, $S_s$, $\lambda_m$, $\rho$, $c$, $q_l$ et $q_s$. Il est impossible de remonter à tout ces paramètres. Le fait que le profil ne dépende que du quintuplet ($\kappa$, $\beta$, $\gamma$, $\zeta$, $\phi$) nous montre qu'il est impossible de remonter à tous les paramètres physiques. En effet plusieurs jeux de paramètres physiques sont équivalents car ils donnent le même quintuplet.

## 1. Discrétisation de l'équation de la charge hydraulique ($\tilde{H}$)

### 1.1. Rappel de l'équation adimensionnelle

$$
\gamma \cdot \frac{\partial \tilde{H}}{\partial \tilde{t}} = \frac{\partial^2 \tilde{H}}{\partial \tilde{z}^2} + \zeta
$$

### 1.2. Discrétisation spatio-temporelle

- **Espace :** $\tilde{z} \in [0, 1]$ est divisé en $N$ cellules, $\Delta\tilde{z} = 1/N$. Indice $k \in \{0, ..., N-1\}$.
- **Temps :** Pas de $\Delta\tilde{t}$. Indice $j$.
- **Variable :** $\tilde{H}_k^j$.

### 1.3. Application du schéma de Crank-Nicolson

$$
\gamma_k \frac{\tilde{H}_k^{j+1} - \tilde{H}_k^j}{\Delta\tilde{t}} = \alpha \left( \frac{\tilde{H}_{k+1}^{j+1} - 2\tilde{H}_k^{j+1} + \tilde{H}_{k-1}^{j+1}}{(\Delta\tilde{z})^2} \right) + (1-\alpha) \left( \frac{\tilde{H}_{k+1}^{j} - 2\tilde{H}_k^{j} + \tilde{H}_{k-1}^{j}}{(\Delta\tilde{z})^2} \right) + \zeta_k
$$

### 1.4. Réorganisation en système matriciel : $A \cdot \vec{\tilde{H}}^{j+1} = B \cdot \vec{\tilde{H}}^{j} + \vec{c}$

#### Coefficients de la matrice A (implicite)

- **Diagonale principale ($A_{k,k}$):**
  $$
  \text{diag}(A)_k = \frac{\gamma_k}{\Delta\tilde{t}} + \frac{2\alpha}{(\Delta\tilde{z})^2}
  $$
- **Diagonales inférieure et supérieure ($A_{k,k-1}, A_{k,k+1}$):**
  $$
  \text{sub/sup}(A)_k = -\frac{\alpha}{(\Delta\tilde{z})^2}
  $$

#### Coefficients de la matrice B (explicite)

- **Diagonale principale ($B_{k,k}$):**
  $$
  \text{diag}(B)_k = \frac{\gamma_k}{\Delta\tilde{t}} - \frac{2(1-\alpha)}{(\Delta\tilde{z})^2}
  $$
- **Diagonales inférieure et supérieure ($B_{k,k-1}, B_{k,k+1}$):**
  $$
  \text{sub/sup}(B)_k = \frac{1-\alpha}{(\Delta\tilde{z})^2}
  $$

#### Vecteur C (source et conditions aux limites)

Le vecteur $\vec{c}$ contient le terme de flux latéral $\zeta_k$ et les termes des conditions aux limites.

$$
c_k = \zeta_k + (\text{Termes des C.L.})
$$

## 2. Discrétisation de l'équation de la température ($\tilde{\theta}$)

### 2.1. Rappel de l'équation adimensionnelle

$$
\beta \cdot \frac{\partial \tilde{\theta}}{\partial \tilde{t}} = \kappa \cdot \frac{\partial \tilde{H}}{\partial \tilde{z}} \cdot \frac{\partial \tilde{\theta}}{\partial \tilde{z}} + \frac{\partial^2 \tilde{\theta}}{\partial \tilde{z}^2} + \phi
$$

### 2.2. Application du schéma de Crank-Nicolson

En appliquant la même pondération $\alpha$ et $(1-\alpha)$ à tous les termes spatiaux :

$$
\beta_k \frac{\tilde{\theta}_k^{j+1} - \tilde{\theta}_k^j}{\Delta\tilde{t}} = \alpha \left[ \left(\kappa G \frac{\partial \tilde{\theta}}{\partial \tilde{z}}\right)_{k}^{j+1} + \left(\frac{\partial^2 \tilde{\theta}}{\partial \tilde{z}^2}\right)_{k}^{j+1} \right] + (1-\alpha) \left[ \left(\kappa G \frac{\partial \tilde{\theta}}{\partial \tilde{z}}\right)_{k}^{j} + \left(\frac{\partial^2 \tilde{\theta}}{\partial \tilde{z}^2}\right)_{k}^{j} \right] + \phi_k
$$

_(Où $G_k^j = (\partial \tilde{H} / \partial \tilde{z})_k^j$ est le gradient de charge connu au temps $j$)_

### 2.3. Réorganisation en système matriciel : $A \cdot \vec{\tilde{\theta}}^{j+1} = B \cdot \vec{\tilde{\theta}}^{j} + \vec{c}$

Les matrices $A$ et $B$ sont **identiques à celles de la dérivation précédente**. Le nouveau terme $\phi_k$ est une source qui ne dépend ni de $\tilde{\theta}^{j+1}$ ni de $\tilde{\theta}^{j}$. Il rejoint donc le vecteur $\vec{c}$.

#### Coefficients des matrices A et B (inchangés)

- **Matrice A (implicite) :**
  $$
  \text{diag}(A)_k = \frac{\beta_k}{\Delta\tilde{t}} + \frac{2\alpha}{(\Delta\tilde{z})^2}
  $$
  $$
  \text{sub}(A)_k = -\frac{\alpha}{(\Delta\tilde{z})^2} + \frac{\alpha \kappa_k G_k^{j}}{2\Delta\tilde{z}}
  $$
  $$
  \text{sup}(A)_k = -\frac{\alpha}{(\Delta\tilde{z})^2} - \frac{\alpha \kappa_k G_k^{j}}{2\Delta\tilde{z}}
  $$
- **Matrice B (explicite) :**
  $$
  \text{diag}(B)_k = \frac{\beta_k}{\Delta\tilde{t}} - \frac{2(1-\alpha)}{(\Delta\tilde{z})^2}
  $$
  $$
  \text{sub}(B)_k = \frac{1-\alpha}{(\Delta\tilde{z})^2} - \frac{(1-\alpha) \kappa_k G_k^{j}}{2\Delta\tilde{z}}
  $$
  $$
  \text{sup}(B)_k = \frac{1-\alpha}{(\Delta\tilde{z})^2} + \frac{(1-\alpha) \kappa_k G_k^{j}}{2\Delta\tilde{z}}
  $$

#### Vecteur C (source et conditions aux limites)

Le vecteur $\vec{c}$ contient le nouveau terme de source $\phi_k$ et les termes des conditions aux limites.

$$
c_k = \phi_k + (\text{Termes des C.L.})
$$
