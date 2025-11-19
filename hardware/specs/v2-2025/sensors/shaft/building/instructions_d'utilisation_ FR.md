# Instructions relatives à la conception et l'impression de la tige MoLoNaRi

Ce dossier contient les fichiers relatifs aux différents versions imprimables de la tige MoLoNaRi. On propose à chaque fois le fichier au format stl, prêt à imprimer ainsi que les fichiers ayant servi à sa conception, soit via le logiciel en ligne *OnShape*, soit via le logiciel *Autodesk Fusion*

## Tige à vis

La tige à vis a été conçue pour être imprimable avec de petites imprimantes (dès 25 cm de haut). La tige doit être imprimée en trois parties, qui se vissent les unes avec les autres. Cela crée des fragilités, le vissage doit donc être effectué avec délicatesse, et bien droit, jusqu'à ce que les capteurs soient correctement alignés. Cela oblige également à avoir un diamètre intérieur plus petit (4 mm) que pour la version sans vis (8 mm) pour plus de solidité

### Instructions pour l'impression :

Imprimer les 3 fichiers situés à l'adresse ```tige à vis/fichiers stl (pour l'impression)```. Le matériau utilisé dans les tests était du polylite ASA, avec un remplissage de 50%. **Avant de lancer l'impression**, il faut s'assurer qu'il n'y a pas de support à l'intérieur des emplacements pour les vis. Ceux-ci étant assez longs, il est très difficile de retirer les supports une fois imprimés.

Une fois imprimés, visser **délicatement** et bien droits les différentes parties. Il n'y a pas besoin de forcer, les emplacements pour les capteurs et les câbles doivent s'aligner conformément à ce qui est fait au niveau de la pièce centrale.

On passe ensuite une couche de résine epoxy pour imperméabiliser la tige, particulièrement au niveau des connexions entre les pièces. **Attention à ne pas boucher les fentes** en bas de la tige qui permettent à l'eau de rentrer. Si la tige est posée sur l'embout au cours du séchage, on fera également attention à protéger les cannelures pour éviter que la résine n'affecte leur capacité à retenir le tuyau branché dessus.

### Instructions pour la modification : 

Sur *OnShape*, faire partie de la classe Géosciences permet d'accéder et de modifier le fichier suivant : https://cad.onshape.com/documents/4a79ee684177de976d1be71a/w/949cad58e65f625d82ab492a/e/a4076a42bb3897534a0d6742?renderMode=0&uiState=690dbe09af6c9c1fde11bd14

Les assemblages pour cette version de la tige sont dans le dossier tige V3. Ces assemblages sont constitués de trois éléments : 

- Le bouchon, issu du fichier bouchon V1 situé à l'adresse tige V2/bouchon V1 (du document précédent)

- Les anneaux qui constituent le corps de la tige, situés à cette adresse : https://cad.onshape.com/documents/f25fb016556e7581687c0c19/w/b619aacd28eccbe013f3ac10/e/4f34b3ff34e84de3f9b1cbe0?renderMode=0&uiState=690dbfc32f6a63784afb96a5 (faire partie de la classe Géosciences permet de modifier le document)

- L'embout cannelé, situé à cette adresse : https://cad.onshape.com/documents/124e26851651926b11e56137/w/e29211a5e8e022dd32264794/e/e55c5a8014cef79f2ee4188a?renderMode=0&uiState=690dc0601fd5c92168290aae (faire partie de la classe Géosciences permet de modifier le document)

Le filetage des vis est fait via le logiciel *AutoDesk Fusion*. Les fichiers correspondant sont dans ```tige à vis/modèles fusion```

## Tige full (sans vis)

Cette version de la tige est conçue pour celle.ux qui disposent d'imprimantes suffisament grandes pour imprimer la tige en une seule fois (la tige mesure 46,3 cm au total). Cela évite les fragilités au niveau des connexions entre les pièces et permet d'avoir un diamètre intérieur de 8 mm. **Le projet MoLoNaRi ne disposant pas à ce stage d'une imprimante de taille suffisante, cette version complète n'a pas pu être testée**

### Instructions pour l'impression

Imprimer le fichier ```tige full (sans vis) - fichier à imprimer.stl```. Le matériau utilisé est du Polylite ASA, avec un remplissage de 50%.

Une fois imprimée, il sera peut-être nécessaire d'ajouter une couche de résine epoxy pour imperméabiliser la tige, le retrait du support après impression pouvant ajouter des porosités plus ou moins importantes. Dans ce cas, prendre garde à ne pas boucher les fentes situées en bas de la tige, et à ne pas abimer les cannelures sur lesquels doit le tuyau est branché

### Instructions de modifications

Sur *OnShape*, faire partie de la classe Géosciences permet de modifier le document suivant : https://cad.onshape.com/documents/4a79ee684177de976d1be71a/w/949cad58e65f625d82ab492a/e/a4076a42bb3897534a0d6742?renderMode=0&uiState=690dbe09af6c9c1fde11bd14; Les fichiers relatifs à la conception de cette version de la tige sont dans le dossier Tige V3 full