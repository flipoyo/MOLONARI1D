# Readme-code-2D
Contient les informations qui décrivent le fonctionnement de la résolution numérique en 2D des équations de Molonari pour implémenter un terme de flux latéral

### But

Le but du nouveau code est d'ajouter la contribution des flux d'eau latéraux à nos équations de température et de charge. L'équipe de 2024 avait pour cela rajouté un terme source volumique q dans l'équation 1D, ce qui ne fait pas de sens selon nous car le flux d'eau ne fait que transiter de droite à gauche (ou de gauche à droite) de l'aquifère, le bilan total net sur le capteur est donc nul si l'on isole une tranche dz pour réaliser le bilan (même quantité entrante et sortante).


### Discrétisation

Nous proposons donc une nouvelle approche, plus rigoureuse physiquement. Les équations seront traitées en 2D sur un maillage régulier qui sera centrée sur notre capteur. Il sera considéré fin en largeur, le but n'étant pas de résoudre en 2D sur toute l'aquifère. Les points supplémentaires en largeur sont donc des intermédiaires de calcul qui nous permettront d'implémenter le flux latéral d'eau comme une condition de Neumann sur notre maillage. Les équations traitées sont les suivantes :

$$S_s \frac{\partial H}{\partial t} = K \Delta H$$ 
$$\frac{\partial T}{\partial t} = \kappa_e \Delta T + \alpha_e \nabla H \cdot \nabla T$$

Pour les traiter, on utilise comme précedemment un schéma de Crank-Nicolson régi par un paramètre $\alpha$ tel que le schéma soit explicite pour $\alpha=1$ et implicite pour $\alpha=0$. Pour les variables, on utilisera la notation suivante $U^{n}_{i,j}$ avec n l'indice temporel, i l'indice de l'axe z vertical, et j l'indice de l'axe x horizontal.
Les discrétisations sont les suivantes :

$$S_s \frac{H_{i,j}^{n+1} - H_{i,j}^{n}}{\Delta t} = \alpha K \left[ \frac{H_{i+1,j}^n - 2H_{i,j}^n + H_{i-1,j}^n}{(\Delta z)^2} + \frac{H_{i,j+1}^n - 2H_{i,j}^n + H_{i,j-1}^n}{(\Delta x)^2} \right] + (1-\alpha) K \left[ \frac{H_{i+1,j}^{n+1} - 2H_{i,j}^{n+1} + H_{i-1,j}^{n+1}}{(\Delta z)^2} + \frac{H_{i,j+1}^{n+1} - 2H_{i,j}^{n+1} + H_{i,j-1}^{n+1}}{(\Delta x)^2} \right]$$

$$ \frac{T_{i,j}^{n+1} - T_{i,j}^{n}}{\Delta t} = \alpha \{ \kappa_e [ \frac{T_{i+1,j}^n - 2T_{i,j}^n + T_{i-1,j}^n}{(\Delta z)^2} + \frac{T_{i,j+1}^n - 2T_{i,j}^n + T_{i,j-1}^n}{(\Delta x)^2} ] + \alpha_e [ (\frac{H_{i+1,j}^n - H_{i-1,j}^n}{2\Delta z})(\frac{T_{i+1,j}^n - T_{i-1,j}^n}{2\Delta z}) + (\frac{H_{i,j+1}^n - H_{i,j-1}^n}{2\Delta x})(\frac{T_{i,j+1}^n - T_{i,j-1}^n}{2\Delta x}) ] \} + (1-\alpha) \{ \kappa_e [ \frac{T_{i+1,j}^{n+1} - 2T_{i,j}^{n+1} + T_{i-1,j}^{n+1}}{(\Delta z)^2} + \frac{T_{i,j+1}^{n+1} - 2T_{i,j}^{n+1} + T_{i,j-1}^{n+1}}{(\Delta x)^2} ] + \alpha_e [ (\frac{H_{i+1,j}^n - H_{i-1,j}^n}{2\Delta z})(\frac{T_{i+1,j}^{n+1} - T_{i-1,j}^{n+1}}{2\Delta z}) + (\frac{H_{i,j+1}^n - H_{i,j-1}^n}{2\Delta x})(\frac{T_{i,j+1}^{n+1} - T_{i,j-1}^{n+1}}{2\Delta x}) ] \} $$ 



### Conditions initiales

Rajouter une dimension rajoute des conditions aux limites. Etant donné que le capteur ne donne qu'une mesure selon z, on ne peut pas être précis sur la dimension selon x. C'est pourquoi on considérera que notre grille est fine selon x. Ainsi, on peut considérer que l'interpolation de Lagrange et l'interpolation linéaire réalisée l'année dernière pour avoir le profil initial selon z peut s'étendre à tout x. On a donc le même profil que précedemment (interpolation d'ordre 5 sur les 5 mesures de température et Linéaire entre les deux mesures de charge pour H).

$$\begin{cases}
H(z, {x}, t=0) \\ 
T(z, {x}, t=0) 
\end{cases} \quad
\text{ Ne dependent pas de x, calcules par interpolation sur les points de mesure initiaux au profondeur discretes}
$$ 


### Conditions aux limites 

De même pour les conditions aux limites de température, on considérera que les conditions de Dirichlet utilisées à la surface et à la profondeur maximale sont étendables pour tout x.
Pour les bords latéraux de notre maillage, on considérera une condition de Neumann constante. On impose un flux uniforme $q_L$ d'eau de température $T_L$ à gauche. Par conservation du flux sur une tranche infinitésimal (la largeur du maillage étant négligeable devant la longueur), on a que le flux entrant latéral est le flux sortant latéral de l'autre côté.

$$\text{Bords up and down, conditions de Dirichlet} \quad \begin{cases} T(z=0,x,t) = T_{riv}(t) \\ T(z=h,x,t) = T_{aq}(t) \end{cases}$$

$$\text{Bords lateraux, conditions de Neumann} \quad \begin{cases} T_{i,-1} = T_{i,1} - \frac{2\Delta x \cdot \rho_w c_w q_L}{\kappa_e} (T_L - T_{i,0}) \\ \kappa_e \frac{T_{i,N_x} - T_{i,-1}}{2\Delta x} = \rho_w c_w q_L (T_L - T_{i,0}) \end{cases}$$


### Traitement numérique

La discrétisation dictée précédemment peut se mettre sous la forme $A(\alpha) X^{n+1}=A^{'}(\alpha)X^{n}$. On choisira de dérouler l'espace selon les lignes de notre maillage. La matrice A est donc de taille $(N_x N_z)^{2}$, et le point $(i,j)$ sera donc indicé $k = I N_x + j$ dans le vecteur déroulé.
On cherche à résoudre $A X^{n+1}=B(X^{n})$. La matrice A étant constante, on ne calculera qu'une seule fois sa décomposition LU. Ensuite, on appliquera successivement toutes les 15 minutes (temps de mesure) l'algorithme de scipy en actualisant le vecteur $B(X^{n})$ qui dépend de l'état précédent et des conditions aux limites. Le code renvoie la valeur de température en $x = L_x / 2$ car la seule chose qui nous intéresse est ce qui passe au niveau du capteur, les autres points étant uniquement des intermédiaires physiques de calcul.
