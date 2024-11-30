# Ajout du paramètre `q`
MOLONARI 2024 : Antoine Bourel de la Roncière, Ombline Brunet et Jordy Steven Hurtado Jimenez


## Changements effectués :  
1. **Ajout du paramètre `q`**  
   - **Fichiers modifiés** :  
     - `params.py` : ajout du paramètre `q` .  
     - `layers.py` : intégration du paramètre dans les couches.  
     - `core.py` : création d'une liste `q_list` à appeler dans les classes `H_stratified` et `T_stratified`
     - `linear_system.py` : utilisation des equations avec `q_list`en ce qui concerne `H_stratified` et `T_stratified`.

2. **Problème à résoudre** :  
   - Il manque demontrer la convergence correcte avec le MCMC.
   - Éviter de créer une nouvelle couche dans `layers` ou dans `compute_solve` uniquement pour gérer le paramètre `heat_depth`. Ceci dans le cas où l'on travaille avec un nouveau paramètre de position dans une cellule. 

   ## Travail en cours :  
- **Test des paramètres avec MCMC** :  
  - Vérification de la convergence correcte du modèle.  
  ## Remarques supplémentaires :  
Pour mieux comprendre les modifications, recherchez `q_list` dans le code principal `core.py`.