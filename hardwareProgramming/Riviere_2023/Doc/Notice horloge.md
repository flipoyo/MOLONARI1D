# Horodatage des données et utilisation des horloges


## Pourquoi ?

La carte Arduino utilisée possède une RTC interne qui permet d'accéder au temps qui s'est écoulé DEPUIS l'allumage de la carte, c'est donc un temps relatif et non absolu. Afin d'obtenir la date et l'heure réels on utilise une horloge externe qui fait parti de l'Adalogger. 

## Comment ?

On demande à l'horloge externe après chaque allumage la date actuelle (`.now()`) qui permet ensuite d'initialiser l'horloge interne (`.setDate()` et `.setTime()`). L'horloge interne est ensuite capable de mesurer le temps écoulé et donc d'horodater les mesures.  
Attention à ne pas utiliser `.millis()` qui overflow sur la durée de la mission et surtout qui ne compte pas le temps écoulé lors de la mise en veille de la carte.

## La suite ?

Le but à terme est de demander l'heure au serveur et donc de s'affranchir du module RTC externe. C'est pourquoi le code ne demande pas constamment la date et l'heure au module RTC externe.

## Liens utiles :


Real Time Clock externe : Adafruit Adalogger FeatherWing, RTC_PCF8523  
Lien de la doc (RTClib) : https://adafruit.github.io/RTClib/html/class_r_t_c___p_c_f8523.html  
Branchements : https://learn.adafruit.com/adafruit-adalogger-featherwing/pinouts

RTC interne, l'horloge qui est dans la carte Arduino MKR WAN 1310  
Lien de la doc RTCZero : https://www.arduino.cc/reference/en/libraries/rtczero/  
Attention la doc est très (très) sommaire !

