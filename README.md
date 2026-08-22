# Enterprise Network Lab

Labo réseau d'entreprise multi-site (HQ + 2 branches), conçu et implémenté intégralement dans **Cisco Packet Tracer**, avec une couche d'automatisation Python (Netmiko + NAPALM).

## 1. Project Overview

Ce projet simule un réseau d'entreprise réaliste à trois sites (siège + deux branches), couvrant la segmentation VLAN, le routage inter-VLAN, le routage dynamique multi-area (OSPF), la sécurité de base (ACL), la traduction d'adresses (NAT), l'attribution automatique d'IP (DHCP), la supervision (SNMP), et une couche d'automatisation en Python.

Le projet est construit **exclusivement en Cisco Packet Tracer** — aucun GNS3, EVE-NG, ou matériel physique n'a été utilisé pour la partie réseau. Les limites que cela impose sont documentées explicitement tout au long de ce document plutôt que dissimulées.

## 2. Objectives

- Concevoir et déployer une topologie d'entreprise multi-site réaliste et portfolio-worthy
- Démontrer une maîtrise pratique de la commutation (VLAN, trunking), du routage (inter-VLAN, OSPF multi-area), de la sécurité (ACL), du NAT, du DHCP et du SNMP
- Construire une couche d'automatisation Python crédible (Netmiko, NAPALM), avec une séparation honnête entre ce qui tourne réellement et ce qui est démontré/validé autrement
- Produire une documentation et un historique Git dignes d'être présentés à un recruteur ou un ingénieur réseau

## 3. Network Architecture

Design hub-and-spoke : HQ concentre la fonction cœur/distribution (switch L3 pour le routage inter-VLAN) et se connecte à deux branches via des liens WAN série point-à-point. Chaque branche route ses VLANs localement via router-on-a-stick et fait office de routeur de bordure OSPF (ABR).

Un bloc "Internet" simulé (R-ISP + Server-Internet) est connecté à R-HQ pour démontrer une sortie NAT réaliste, hors du domaine de routage interne.

## 4. Topology

```
                         ┌─────────────────────────┐
                         │           HQ              │
                         │  SW-HQ-ACCESS (2960, L2)  │
                         │        │ trunk             │
                         │  SW-HQ-CORE (3560, L3)     │
                         │   VLAN10/20/30 + OSPF      │
                         │        │ transit           │
                         │      R-HQ (2911) ── Gig0/1 ── R-ISP ── Server-Internet
                         └────┬─────────────┬─────────┘        (Internet simulé)
                     Serial   │             │  Serial
                    (Area 0)  │             │  (Area 0)
                    ┌─────────▼───┐   ┌─────▼────────┐
                    │  R-Branch1  │   │  R-Branch2   │
                    │  ABR Area1  │   │  ABR Area2   │
                    │      │      │   │      │       │
                    │ SW-Branch1  │   │ SW-Branch2   │
                    └─────────────┘   └──────────────┘
```

Voir `topologies/drawio/` pour le schéma complet avec adressage, et `topologies/packet-tracer/` pour le fichier `.pkt`.

## 5. Device Inventory

|Nom|Modèle|Site|Rôle|
|---|---|---|---|
|R-HQ|Cisco 2911 (+ 2x WIC-2T)|HQ|Routeur de bordure WAN, OSPF backbone, NAT|
|SW-HQ-CORE|Cisco 3560 (L3)|HQ|Cœur, inter-VLAN routing, OSPF Area 0|
|SW-HQ-ACCESS|Cisco 2960 (L2)|HQ|Accès utilisateurs/serveurs|
|SRV-HQ|Server-PT|HQ|Service DHCP pour VLAN20|
|PC-HQ-1, PC-HQ-2|PC-PT|HQ|Postes de test|
|R-Branch1|Cisco 1941 (+ WIC-2T)|Branch1|Router-on-a-stick, ABR Area 1, DHCP local|
|SW-Branch1|Cisco 2960 (L2)|Branch1|Accès utilisateurs|
|PC-Branch1-1, PC-Branch1-2|PC-PT|Branch1|Postes de test|
|R-Branch2|Cisco 1941 (+ WIC-2T)|Branch2|Router-on-a-stick, ABR Area 2, DHCP local|
|SW-Branch2|Cisco 2960 (L2)|Branch2|Accès utilisateurs|
|PC-Branch2-1, PC-Branch2-2|PC-PT|Branch2|Postes de test|
|R-ISP|Router (2911)|Internet (simulé)|Simule le FAI, hors domaine OSPF|
|Server-Internet|Server-PT|Internet (simulé)|Cible externe pour valider le NAT|

## 6. VLAN Plan

|Site|VLAN ID|Nom|Usage|
|---|---|---|---|
|HQ|10|MGMT|Management des équipements|
|HQ|20|USERS|Postes utilisateurs|
|HQ|30|SERVERS|Serveurs (SRV-HQ)|
|HQ|99|NATIVE|VLAN natif du trunk (inutilisé)|
|Branch1|10|MGMT|Management|
|Branch1|20|USERS|Postes utilisateurs|
|Branch1|99|NATIVE|VLAN natif du trunk (inutilisé)|
|Branch2|10|MGMT|Management|
|Branch2|20|USERS|Postes utilisateurs|
|Branch2|99|NATIVE|VLAN natif du trunk (inutilisé)|

## 7. IP Addressing Plan

|Réseau|Sous-réseau|Passerelle|
|---|---|---|
|HQ VLAN10 (Mgmt)|10.10.10.0/24|.1 sur SW-HQ-CORE|
|HQ VLAN20 (Users)|10.10.20.0/24|.1 sur SW-HQ-CORE|
|HQ VLAN30 (Servers)|10.10.30.0/24|.1 sur SW-HQ-CORE|
|Transit SW-HQ-CORE ↔ R-HQ|10.10.99.0/30|—|
|WAN R-HQ ↔ R-Branch1|10.0.12.0/30|—|
|WAN R-HQ ↔ R-Branch2|10.0.13.0/30|—|
|Branch1 VLAN10 (Mgmt)|10.20.10.0/24|.1 sur R-Branch1|
|Branch1 VLAN20 (Users)|10.20.20.0/24|.1 sur R-Branch1|
|Branch2 VLAN10 (Mgmt)|10.30.10.0/24|.1 sur R-Branch2|
|Branch2 VLAN20 (Users)|10.30.20.0/24|.1 sur R-Branch2|
|WAN R-HQ ↔ R-ISP (outside)|200.100.100.0/30|—|
|R-ISP ↔ Server-Internet|203.0.113.0/24|.1 sur R-ISP|

Logique d'adressage : `10.10.x` = HQ, `10.20.x` = Branch1, `10.30.x` = Branch2, `10.0.x` = liens WAN internes.

## 8. Routing Architecture

- **HQ** : routage inter-VLAN centralisé sur SW-HQ-CORE (SVIs), R-HQ ne gère que le WAN et la sortie Internet
- **Branches** : router-on-a-stick (sous-interfaces 802.1Q) sur R-Branch1/R-Branch2, pas de switch L3 dédié — choix réaliste pour un petit site
- **Route par défaut** : configurée statiquement sur R-HQ (`ip route 0.0.0.0 0.0.0.0 200.100.100.2`), propagée à tout le domaine OSPF via `default-information originate`

## 9. OSPF Multi-Area Design

|Area|Contenu|Rôle|
|---|---|---|
|Area 0 (Backbone)|Transit HQ (10.10.99.0/30), liens WAN (10.0.12.0/30, 10.0.13.0/30), VLANs HQ|R-HQ et SW-HQ-CORE|
|Area 1|VLANs Branch1 (10.20.10.0/24, 10.20.20.0/24)|R-Branch1 = ABR|
|Area 2|VLANs Branch2 (10.30.10.0/24, 10.30.20.0/24)|R-Branch2 = ABR|

Validé par `show ip ospf neighbor` (voisinages FULL sur tous les liens) et `show ip route ospf` (routes `O` intra-area et `O IA` inter-area cohérentes). R-ISP est volontairement **hors** du domaine OSPF — il simule un FAI externe qui ne connaît que l'IP publique de R-HQ.

## 10. ACL Design

Règle de segmentation de sécurité : **VLAN20 (USERS) ne peut pas atteindre VLAN10 (MGMT)**, appliquée sur SW-HQ-CORE.

```
ip access-list extended BLOCK-USERS-TO-MGMT
 deny ip 10.10.20.0 0.0.0.255 10.10.10.0 0.0.0.255
 permit ip any any

interface Vlan20
 ip access-group BLOCK-USERS-TO-MGMT in
```

Placement : le plus près possible de la source du trafic à bloquer (interface Vlan20, en entrée), pour économiser les ressources de traitement. Validé par ping échoué vers VLAN10 et compteurs de matches sur `show access-lists`.

## 11. NAT Design

NAT Overload (PAT) sur R-HQ, traduisant tout le trafic interne (`10.0.0.0/8`) vers l'IP publique unique `200.100.100.1` en sortie vers R-ISP.

```
ip access-list standard NAT-INSIDE-NETWORKS
 permit 10.0.0.0 0.255.255.255

interface GigabitEthernet0/1
 ip nat outside

! Gig0/0, Se0/3/0, Se0/3/1 : ip nat inside

ip nat inside source list NAT-INSIDE-NETWORKS interface GigabitEthernet0/1 overload
```

Validé par ping réussi depuis des PC de chaque site vers `Server-Internet` (203.0.113.10), et `show ip nat translations` confirmant les traductions actives.

## 12. DHCP Design

|Site|Méthode|Détails|
|---|---|---|
|HQ (VLAN20)|Serveur dédié (SRV-HQ)|`ip helper-address 10.10.30.10` sur la SVI Vlan20 de SW-HQ-CORE (relay DHCP inter-VLAN)|
|Branch1 (VLAN20)|Pool local sur R-Branch1|`ip dhcp pool BRANCH1-USERS`, réseau 10.20.20.0/24|
|Branch2 (VLAN20)|Pool local sur R-Branch2|`ip dhcp pool BRANCH2-USERS`, réseau 10.30.20.0/24|

VLAN10 (MGMT) et VLAN30 (SERVERS) restent en IP statique par choix — les équipements réseau et serveurs ne doivent jamais changer d'IP automatiquement.

## 13. SNMP / Monitoring

SNMPv2c configuré sur R-HQ (`snmp-server community NetLab-RO RO`), interrogé avec succès depuis le MIB Browser intégré de Packet Tracer sur PC-HQ-1 :

- `sysDescr` → confirmé (modèle/version IOS)
- `sysUpTime` → confirmé (uptime réel)
- `sysName` → confirmé (`R-HQ`)
- `sysContact` / `sysLocation` → non configurés (volontaire, hors périmètre du test)

Voir section 17 pour les limitations SNMP de Packet Tracer.

## 14. Python Automation

Dossier `scripts/`, deux approches démontrées :

**Netmiko** (`scripts/netmiko/`) :

- `connect.py` — connexion SSH de base, lecture d'inventaire (`devices.yaml`), envoi d'une commande `show`, logging, gestion d'erreurs (auth, timeout)
- `deploy_config.py` — déploiement de configuration à tous les équipements de l'inventaire, sauvegarde des running-configs dans `configs/<site>/`, isolation des erreurs par device (un échec n'arrête pas les autres)

**NAPALM** (`scripts/napalm/`) :

- `get_facts.py` — récupération d'informations structurées (dict Python) via `get_facts()`, sans parsing manuel de texte — différence clé avec Netmiko

**Tests** (`scripts/*/tests/`) : suite de tests avec `unittest.mock`, validant la logique de chaque script sans dépendre d'un équipement réel.

### Étiquetage A/B/C (limitation Packet Tracer)

- **A. Implémenté dans Packet Tracer** : les équipements existent, sont configurés et fonctionnels
- **B. Démontré en Python** : logique de connexion/déploiement complète, validée par tests avec mock
- **C. Prévu pour déploiement réel** : ces scripts se connecteraient tels quels à du matériel Cisco réel ou un sandbox Cisco DevNet, sans aucune modification — Packet Tracer ne fournit pas d'API/serveur SSH accessible depuis un outil externe

## 15. Testing and Validation

|Test|Résultat|
|---|---|
|Inter-VLAN routing HQ (VLAN20 ↔ VLAN30)|✅ 5/5|
|Voisinages OSPF (3 liens)|✅ FULL sur les 3|
|Routes inter-area (`O IA`) présentes|✅|
|Ping HQ → Branch1 / Branch2|✅ 5/5|
|DHCP (HQ relay + branches locales)|✅ baux attribués (`show ip dhcp binding`)|
|ACL (blocage USERS → MGMT)|✅ deny confirmé par compteur de matches|
|NAT (PC interne → Server-Internet)|✅ 5/5, traductions visibles|
|SNMP polling (MIB Browser)|✅ sysDescr/sysUpTime/sysName récupérés|
|Scripts Python (tests unitaires mock)|✅ 9 tests, tous verts|

## 16. Troubleshooting

Problèmes rencontrés et résolus pendant le projet (conservés comme valeur pédagogique) :

- **`switchport mode trunk` refusé sur le 3560** : nécessite `switchport trunk encapsulation dot1q` avant, contrairement au 2960 qui n'a qu'une seule encapsulation possible.
- **`%CDP-4-NATIVE_VLAN_MISMATCH`** : le native VLAN du trunk doit être identique des deux côtés — survenu le temps de configurer les deux extrémités.
- **Port routé sur switch L3 resté `unassigned`** : un port de switch L3 reste en mode switchport par défaut ; nécessite `no switchport` avant de lui donner une IP.
- **`show ip protocols` vide en attendant les voisins** : normal avant que le voisin en face ait sa propre config OSPF — pas une erreur.
- **`Activate.ps1` bloqué par PowerShell** : politique d'exécution Windows par défaut ; résolu avec `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
- **`show snmp community` : commande invalide** : n'existe pas sous cette forme en IOS classique ; utiliser `show running-config | include snmp` ou `show snmp` à la place.

## 17. Packet Tracer Limitations

Limitations rencontrées et documentées tout au long du projet, sans les dissimuler :

- **Netmiko / NAPALM** : aucune connexion SSH réelle possible depuis un outil externe vers un équipement Packet Tracer — validé uniquement via tests avec mock, conçu pour du Cisco IOS réel ou un sandbox DevNet.
- **SNMP** : pas de traps/informs configurables. Le polling fonctionne via le MIB Browser intégré de Packet Tracer (confirmé dans ce projet — `sysDescr`, `sysUpTime`, `sysName`), mais un vrai `snmpwalk` externe depuis une VM Linux n'est pas possible.
- **Wireshark** : les captures dans Packet Tracer sont des simulations du moteur PT, pas de vraies captures de paquets — utiles pédagogiquement mais pas identiques à une capture réseau réelle.

## 18. Screenshots

À ajouter dans `docs/screenshots/` :

- Topologie complète Packet Tracer
- `show ip ospf neighbor` sur R-HQ (3 voisins)
- `show ip nat translations` avec traductions actives
- MIB Browser avec résultats SNMP
- `show ip dhcp binding` sur chaque site

## 19. Future Improvements

- Migrer le SNMP en SNMPv3 (authentification + chiffrement) si testé sur un vrai équipement
- Ajouter de la redondance (HSRP/VRRP) sur le core HQ
- Tester les scripts Netmiko/NAPALM contre un sandbox Cisco DevNet réel pour valider une vraie session SSH
- Ajouter Syslog centralisé
- Étendre les ACL avec des règles plus granulaires par service

## 20. Lessons Learned

_(Section à compléter personnellement — ce que tu retiens de la conception, des erreurs corrigées, et de ce que tu referais différemment. C'est la partie que les recruteurs lisent souvent en premier.)_