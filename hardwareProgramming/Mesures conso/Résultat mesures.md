# Résultat des mesures de consommation de courant pour les différents programmes de consommation 

Ce test a permis de déterminer quelles sont les solutions appropriées pour réduire la consommation de notre dispositif.

| Programme de veille utilisé      |   Consommation de courant    |
|:-:    |:-:  |
|**Programme avec juste la carte et l'antenne** |
| Idle    |    10 mA   |
| Sleep   |   0.106 mA   |
| Ecoute radio |  20 mA   |
| Radio Idle|  10.6 mA |
| Radio off |  9 mA |
| Radio reset v1 | 0.40 mA |
| Radio off Pin Pulldown | 0.40 mA --> 5 mA (au bout de 30s, 1 min) |
| Radio off Pin Pullup| 0.40 mA --> 4.6 mA (au bout de 30s, 1 min) |
| Radio reset v2 (version actuelle) | 0.107 mA |
| **Programme sur montage complet** |
|  Main + Extension deep sleep + reset | 30 mA |
| Deep sleep + Extension off |  1 mA |
| Deep sleep + extension avec SD débranchée | 0.1 mA |


## Explication des différents programmes 
| Programme de veille utilisé      |   Effet du programme   |
|:-:    |:-:  |
|**Programme avec juste la carte et l'antenne** |
| Idle    |  La carte arduino reste allumée mais ne fait rien    |
| Sleep   |  On branche l'antenne et on la met directement en mode sleep    |
| Ecoute radio |  On allume la radio et on la met en mode receive   |
| Radio Idle|  On allume la radio et on la met en mode idle |
| Radio off | On allume la radio puis on lance LoRa.end()  |
| Radio reset v1 | On met le pin LoRa reset à low |
| Radio off Pin Pulldown | On met tous les pulls entrées sorties en mode input pulldown |
| Radio off Pin Pullup| On met tous les pulls entrées sorties en mode input pullup |
| Radio reset v2 (version actuelle) | On met LoRa reset à low puis à high |
| **Programme sur montage complet** |
|  Main + Extension deep sleep + reset | Programme rivière 2023 : initalisation puis reset radio(v2) puis on éteint le processeur : on obtient la conso de la carte d'extension (résultat surprenant, expérience à refaire) |
| Deep sleep + Extension off | On a mis le programme sleep en ayant branché les extensions ( on mesure la conso des extensions en veille) |
| Deep sleep + extension avec SD débranchée | même expérience mais avec carte SD débranchée |
