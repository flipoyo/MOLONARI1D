# Rapport d'avancement 2025 — Projet MOLONARI1D

**Date de rédaction** : Décembre 2025  
**Superviseur** : Nicolas Flipo (Mines Paris – PSL)  
**Équipes contributrices** : ITA Groupe 1, ITA Groupe 2, Équipe Matériel (2025), Équipe Calcul Scientifique (2025)

---

## 1. Vue d'ensemble des capacités actuelles du système

MOLONARI1D est un écosystème complet de **surveillance des échanges nappe-rivière**, couvrant l'ensemble de la chaîne, du capteur physique jusqu'à l'analyse scientifique.

### Architecture générale

```
Capteurs sous-marins → Relais → Passerelle → Serveur → Base de données → Outils d'analyse
     (Arduino)          (LoRa)   (LoRaWAN)  (Internet)     (SQL)          (Python ML/GUI)
```

### Composants opérationnels

#### 🔧 Matériel — MOLONARI1D v2.0

Le dispositif v2.0 (développé en 2025) intègre l'ensemble des capteurs dans un seul boîtier :

- **Boîte métallique étanche (IP68)** avec joint, couvercle et lest, validée en immersion en laboratoire
- **5 capteurs de température** (HOBO TMC6 HD — thermistances NTC) montés sur une tige 3D printée, permettant un profil de température sur ~40 cm de sédiment
- **Capteur de pression différentielle** pour mesurer la charge hydraulique à travers le lit de rivière
- **Électronique embarquée** : carte Arduino MKR WAN 1310 + Adalogger FeatherWing (carte SD + RTC), antenne LoRa étanche
- **Autonomie** : 8 à 12 mois sur batterie Li-ion 3,7 V / 5 000 mAh (jusqu'à 2,5 ans mesurés en laboratoire)
- **Relais** : Arduino MKR WAN 1310 avec antenne LoRaWAN, boîte de protection sur berge

#### 📡 Protocoles de communication

- **LoRa local (capteur → relais)** : protocole personnalisé avec poignée de main à trois voies, fenêtres de communication planifiées (ex. : 23 h 45 quotidiennement), mécanisme de reprise exponentielle (6 tentatives max), validation par checksum
- **LoRaWAN (relais → passerelle)** : protocole standard OTAA, débit adaptatif, intégration au serveur réseau ChirpStack
- **Internet (passerelle → serveur)** : transmission des données vers un serveur distant et un site web

#### 🔬 pyheatmy — Moteur de calcul scientifique

- **Inversion Bayésienne MCMC** (algorithme de Metropolis–Hastings) pour l'estimation des paramètres physiques du lit de rivière : perméabilité, porosité, conductivité thermique, capacité calorifique
- **Quantification d'incertitude** avec intervalles de confiance sur chaque paramètre
- **Système linéaire adimensionné** pour la stabilité numérique
- **Multi-couches** : modèle 1D stratifié (H_stratified + T_stratified)
- **Multi-chaînes MCMC** avec diagnostic de Gelman-Rubin
- **Inversion sur données réelles** disponible (nouvelle démonstration 2025)
- **Intégration directe** avec les données capteurs issues de Molonaviz

#### 📊 Molonaviz — Interface de gestion et visualisation

- **Interface graphique PyQt5** pour la gestion des dispositifs de surveillance
- **Base de données SQL** pour l'organisation hiérarchique : sites → points d'échantillonnage → capteurs → mesures
- **Pipeline de contrôle qualité** des données brutes capteurs
- **Lancement direct** des workflows d'inversion pyheatmy
- **Calibration des thermomètres** intégrée dans l'interface
- **Gestion des équipements virtuels** (nouvelle fonctionnalité 2025)

#### 🌐 Site web — molonari.io

- Portail d'entrée pour les utilisateurs MOLONARI, accessible à l'adresse `molonari.io`
- Hébergé sur un VPS dédié (Debian 12, LWS), nom de domaine Namecheap
- Interface WordPress, extensible (API dataloggers, MCMC distant, chatbot envisagés)

### Niveau de maturité technologique (TRL)

**TRL actuel : 5–6** — Validation complète en laboratoire, transition vers le déploiement terrain en cours.

| Composant | TRL | Confiance |
|-----------|-----|-----------|
| Capteurs (matériel) | 5–6 | Élevée |
| Relais (matériel) | 5–6 | Élevée |
| Passerelle | 6 | Élevée |
| Firmware capteur | 6 | Élevée |
| Firmware relais | 6 | Élevée |
| Protocole LoRa | 6 | Moyenne–Élevée |
| Intégration LoRaWAN | 6 | Élevée |
| Gestion d'énergie | 6 | Élevée |
| Logiciel scientifique (pyheatmy) | 6–7 | Élevée |
| Interface graphique (Molonaviz) | 6–7 | Élevée |

---

## 2. Avancées 2025

### 2.1 Matériel — Nouvelle version v2.0

**Équipe :** Esther Pautrel, Timothée Babin (ITA Matériel 2025)

La version v2.0 du dispositif, conçue et assemblée en 2025, constitue une évolution majeure par rapport à la v1 :

- **Intégration complète** de tous les capteurs (température + pression) dans un unique boîtier métallique étanche, contre deux dispositifs séparés en v1.
- **Nouveaux capteurs de température** : HOBO TMC6 HD (thermistances NTC), avec calibration expérimentale du paramètre β = 3 834 K ± 0,5 % par régression linéaire sur données de refroidissement.
- **Tige 3D imprimée** redesignée pour maintenir les 5 capteurs de température à des profondeurs précises dans le sédiment.
- **Documentation complète** : spécifications mécaniques, schémas électroniques, guide d'assemblage, photos du dispositif complet.
- **Tests en laboratoire** : le système complet a été validé en immersion dans un bac d'eau en laboratoire (TRL 5 atteint).
- **Audit de coûts** : fichier de synthèse des coûts matériels disponible (`hardware/specs/v2-2025/costs/`).

### 2.2 Firmware — Restructuration et intégration LoRaWAN

**Équipe :** ITA Groupe 1 (2025)

La totalité du code firmware a été refactorisée et modernisée :

- **Migration vers PlatformIO** : l'environnement de développement est désormais géré par PlatformIO (VS Code), permettant une gestion propre des bibliothèques internes et externes via `platformio.ini`.
- **Architecture en bibliothèques** : le code est organisé en bibliothèques indépendantes (`encode`, `LoRa_Molonari`, `LoRaWAN_Molonari`, `Measure`, `Memory_monitor`, `Reader`, `Time`, `Waiter`, `Writer`).
- **Codes démonstration fonctionnels** : `demo_sensor` et `demo_relay` — considérés comme le "golden commit" de référence — permettent de valider l'ensemble de la chaîne de communication.
- **Chaîne complète validée** : capteur → relais → passerelle → serveur → site web, bout en bout.
- **Correction de bug majeur** : double envoi de données résolu grâce à un `seek()` dans le relais et le capteur.
- **Encodage de la tension en température** : correction de la formule de conversion tension → température pour les nouveaux capteurs.
- **Documentation de transition** (`Propective2026-2027.md`) rédigée pour les équipes futures avec les points d'attention clés : gestion du temps RTC, communication multi-capteurs, configuration distante.

### 2.3 Réseau et passerelle — Intégration ChirpStack

**Équipe :** Armand de la Fontenay, ITA Groupe 2 (2025)

- **Configuration complète de la passerelle** sur le serveur réseau ChirpStack, avec documentation détaillée.
- **Réception de l'UID** du capteur par la passerelle pour l'identification des dispositifs.
- **Code de test de payload** fonctionnel pour valider la réception des données LoRaWAN.
- **Séparation architecture** site web / serveur dans le dépôt `molonari.io` pour une meilleure maintenabilité.

### 2.4 Molonaviz — Nouvelles fonctionnalités

**Équipe :** Eulalie Contreras, ITA Groupe 2 (2025)

- **Calibration des thermomètres** : ajout des champs nécessaires à la calibration des thermomètres dans l'interface graphique (`SPointCoordinator`) — fonctions `updateThermometerCalibration`.
- **Correction du warning multi-connexion BD** : résolution d'un avertissement de connexions multiples à la base de données.
- **Interface d'ajout d'équipement virtuel** : nouvelle interface graphique permettant d'ajouter des équipements simulés pour les tests.
- **Amélioration de `db_insertion.py`** : ajout des fonctions `get_sampling_point_name` et `get_study_name`; importation des classes Molonaviz.

### 2.5 pyheatmy — Calcul scientifique

**Équipe :** Noé (ITA Calcul Scientifique 2025), diverses contributions

- **Inversion sur données physiques réelles** : nouvelle démonstration (`demo_genData_real_inversion.ipynb`) réalisant une inversion MCMC sur des données terrain réelles, et non plus uniquement synthétiques.
- **Adimensionnement du système linéaire** (`linear_system_ADIM.py`) : refactorisation complète du solveur thermique/hydraulique en variables adimensionnées pour une meilleure stabilité numérique. Solveur implémenté avec `numba` pour l'accélération.
- **Changement de paramètre de perméabilité** : passage à `moinslog10IntrinK` (opposé du logarithme décimal de la perméabilité intrinsèque) pour une meilleure exploration de l'espace des paramètres.
- **Changement de convention pour DH_0** : mise à jour de la convention initiale pour la charge hydraulique différentielle.
- **Nettoyage du code** : suppression de fichiers CSV temporaires, traduction des commentaires français → anglais, nettoyage du module de calcul adimensionné.
- **Notebook de démonstration mis à jour** pour 2025, intégrant la classe `synthetic_MOLONARI` et la classe `Column`.

### 2.6 Infrastructure et documentation

- **Évaluation TRL** (`TRL_ASSESSMENT.md`) : document formel d'évaluation du niveau de maturité technologique du système (TRL 5–6), rédigé en décembre 2025.
- **Fichier `contributors.md`** : création d'un fichier dédié aux contributeurs étudiants, séparé du README principal.
- **README principal mis à jour** : section "Technology Readiness" ajoutée, rôles des contributeurs précisés, informations sur les connexions électroniques des capteurs.
- **Site web molonari.io** : lancement d'un site officiel du projet (VPS dédié, WordPress), avec guide de déploiement documenté.
- **`.gitignore` amélioré** : ajout de règles pour ignorer les fichiers `libdeps` générés par PlatformIO.

---

## 3. Points d'attention et travaux restants

### Défis techniques identifiés

| Problème | Priorité | Statut |
|----------|----------|--------|
| Propagation du signal LoRa à travers l'eau | Élevée | En cours — tests d'antennes et fréquences alternatives prévus |
| Portée de communication longue distance | Moyenne | Partielle — 800 m atteints vs objectif 2 km+ |
| Fiabilité de la carte SD | Moyenne | Atténuée — bibliothèque Queue, à surveiller en conditions réelles |
| Tests de stress environnemental (glace, crues) | Moyenne | Non réalisés |
| Communication multi-capteurs (1 relais → N capteurs) | Élevée | Conçu mais non implémenté |
| Configuration distante via downlink LoRaWAN | Moyenne | Nécessite remplacement de la passerelle actuelle |
| Dérive des horloges RTC | Moyenne | Documentée, correction hebdomadaire via internet recommandée |

### Prochaines étapes

1. **Déploiement terrain** dans un vrai lit de rivière pour valider le système en conditions opérationnelles (TRL 6 complet).
2. **Implémentation du support multi-capteurs** sur un seul relais.
3. **Optimisation de la communication sous-marine** (antennes, fréquences).
4. **Validation longue durée** de l'autonomie batterie (8–12 mois).
5. **Tests en conditions extrêmes** (gel, crue, chaleur).

---

## 4. Résumé

L'année 2025 a été marquée par une **maturation significative** de l'ensemble de l'écosystème MOLONARI1D. Le système a franchi une étape décisive avec la **validation complète en laboratoire** d'un prototype v2.0 intégré fonctionnant en immersion, atteignant le niveau TRL 5–6. La chaîne de communication bout en bout (capteur → relais → passerelle → serveur) a été démontrée opérationnelle. L'outillage logiciel (pyheatmy, Molonaviz) a été enrichi de fonctionnalités scientifiques avancées et de corrections de robustesse. Le projet dispose désormais d'une présence web officielle (molonari.io). La prochaine étape majeure est le **déploiement in situ** en environnement fluvial réel.

---

*Document rédigé sur la base des contributions et commits du dépôt MOLONARI1D sur la période janvier–décembre 2025.*
