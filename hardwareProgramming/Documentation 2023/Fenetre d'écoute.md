# Fenêtre d'écoute LoRa

## Intro

Quand on envoie un message en LoRa, il faut que le récepteur ait sa radio allumée et qu'il écoute les messages. Le problème c'est qu'écouter ça consomme de l'énergie, trop pour le faire en continu. (ça représente déjà 70% de nos émissions si on écoute 10 s toute les 15 min)  
La solution : l'émetteur et le récepteur se mettent d'accord à l'avance sur le moment où le message sera envoyé. Le récepteur va écouter sur ce petit interval de temps, appelé "fenêtre d'écoute", par exemple 10s, et l'émetteur enverra le message à ce moment.

C'est une fonctionnalité sur laquelle l'équipe capteur 2023 a réflechie, mais n'a pas eu le temps d'implémenter. 

## Fonctionnement

La difficulté est de bien syncroniser l'émetteur et le récepteur. La méthode la plus simple est d'attendre 15 min après la dernière transmission réussie, puis d'écouter 10s.

## Décallage des horloges

Un problème qui va survenir est l'imprécision des horloges des deux cartes. Elles se décalent de quelques secondes par jour l'une par rapport à l'autre (ordre de grandeur à vérifier). Il y a un risque qu'après quelques jours les deux cartes perdent la synchronisation.  

Première solution : Utiliser des références communes  
On utilise la dernière transmission réussie comme point de repère dans le temps commun aux deux cartes. C'est une occasion de les re-syncroniser.  
Comme ça, tant que les deux cartes ont des échanges réguliers, elles restent syncronysées

## Rattrapage

Mais les choses se corsent quand les deux cartes ne peuvent plus communiquer pendant une longue période, par exemple si une crue bloque les communications. Les cartes peuvent alors totalement se décaler l'une par rapport à l'autre.  
Il faudra alors que le récepteur entre dans un mode de "rattrappage", où il va essayer de restaurer la syncro. Pour ça, le récepteur va colontairement prendre du retard pour parcourir plus vite les déphasages entre émetteur et récepteur.  
En pratique, mettons qu'au lieu d'attendre 15 min entre deux fenêtres d'écoute, il va attendre 15 min et 10 s. Si l'émetteur avait pris du retard, le récepteur va le compenser en prenant lui aussi du retard et la connection est rétablie. Et si au contraire l'émetteur était en avance, à force de prendre du retard le récepteur va finir par avoir lui aussi de l'avance sur l'émission suivante, et par retrouver la syncro.