# Arduino-capteurs-molonari

Description des fichiers:


capteurs_sans_tele.ino : code du datalogger enregistrant la pression et les températures sans télétransmission; à téléverser sur une carte Arduino directement reliée par des fils aux capteurs de température et de pression et équipée d'un shield


teletransmission_rive.ino : code du datalogger situé sur la rive dans le cas de la télétransmission ; à téléverser sur une carte Arduino située sur la rive et équipée d'un shield et d'un module de radiofréquence; ce code lit les consignes de mesure écrites sur la carte SD, envoie à l'Arduino "rivière" les instructions indiquant quand il faut effectuer une mesure et enregistre sur un fichier CSV sur la carte SD les résultats de mesure


teletransmission_riviere.ino : code à téléverser sur une carte Arduino qui ira au fond de la rivière, sera reliée aux capteurs et équipée d'un module de radiofréquence ; ce code fait faire les mesures par les capteurs lorsqu'un ordre est reçu de l'Arduino "rive" et renvoie les valeurs mesurées à l'Arduino "rive"


teletransmission_rive_v2.ino et teletransmission_riviere_v2.ino : très similaires aux deux précédents sauf qu'ils utilisent le module de télécommunication wirelessSPI au lieu de radio, ce qui doit permettre la communication d'un plus grand nombre de données à la fois. En effet, les codes précédents permettent seulement la communication de deux variables parmi les 5 (t1,t2,t3,t4,pressure) entre la rivière et la rive; le module wirelessSPI doit permettre la communication des 5 variables. Cependant, ces deux derniers codes n'ont pas encore été testés sur des cartes Arduino, il s'agit d'une modification que nous avons effectuée après la soutenance

Remarques sur l'exécution des codes :


La carte SD insérée dans une carte Arduino doit contenir 2 fichiers CSV : un fichier intitulé "test.csv", qui peut être vide (c'est seulement un fichier qui vise à tester la présence de la carte SD) et un fichier intitulé "test3.csv" qui contient les consignes de mesure au format suivant : 
instant_debut,instant_fin,periode_echantillonnage
où les instants de début et de fin sont écrits sous le format suivant : YYYY:MM:DD:hh:mm:ss
et où la période d'échantillonnage est sous la forme : hh:mm:ss


Attention : les noms de fichiers CSV lus par la carte Arduino ne doivent pas dépasser 8 caractères, sinon le code va planter !
