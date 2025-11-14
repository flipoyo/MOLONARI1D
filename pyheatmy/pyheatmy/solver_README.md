# Readme-solver
Contient les informations qui décrivent l'implémentation du solveur.

Warning : Ce markdown contient des formules latex, une extension sur vs-code est nécessaire pour les visualiser.

### But

Le but du solveur est de résoudre des équations du type $AX = B$ avec A tridiagonale, X et B des vecteurs quelconques.

Factuellement, X est la charge ou la température au temps n+1, A est la matrice des coefficients devant $x^{n+1}$ de l'équation  étudiée, et B est le second membre. B contient les informations sur les coefficients $x^{n}$ et les conditions aux limites.


### Méthode

On commence par appliquer un algorithme du pivot de Gauss pour rendre la matrice triangulaire supérieure. Ensuite, la résolution est triviale en partant de la dernière inconnue.


### Pourquoi ?

On a choisi cette méthode plutôt qu'une décomposition LU suivi d'une résolution avec le solveur de numpy car elle est beaucoup plus efficace. En effet, notre méthode prend en compte les spécificités de la matrice (tridiagonale) et permet donc de résoudre le système en complexité $O(n)$. 

Puisque l'algorithme repose sur des boucles et des opérations arithmétiques intensives sur des tableaux NumPy, la compilation Just-In-Time (JIT) avec Numba permet également d'accélérer drastiquement son exécution.