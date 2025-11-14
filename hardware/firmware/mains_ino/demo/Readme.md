**Voici les différences entre les fichiers de démos et non de démos :**

Les intervalles de fréquence de mesure et d'envoi sont plus courtes dans les fichiers démo : il faut faire attention à modifier les fichiers configs correspondants à chaque fois. 

Par ailleurs, il faut décommenter le temps de sommeil jusqu'à la prochaine mesure / communication en fonction des temps à disposition. (lignes 224 à 234 dabs le demo sensor). 
Dans le demo_relay, il faut augmenter le delay de 1000 à 60000 l152