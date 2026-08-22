"""
get_facts.py — Récupère les infos de base d'un équipement via NAPALM.

Usage :
    NET_USER=admin NET_PASS=secret python get_facts.py R-HQ

Packet Tracer limitation :
    Comme Netmiko, NAPALM a besoin d'un vrai device Cisco IOS
    (matériel réel ou Cisco DevNet Sandbox) — Packet Tracer ne peut
    pas être atteint. Voir tests/test_get_facts.py pour la validation
    avec mock.

Différence avec Netmiko : ici on ne parse rien nous-mêmes, NAPALM
retourne directement un dict Python structuré.
"""

import os
import sys

import yaml
from napalm import get_network_driver


def get_facts(device_name):
    """Se connecte à l'équipement et retourne ses infos de base (dict structuré)."""

    with open("devices.yaml", "r", encoding="utf-8") as f:
        inventory = yaml.safe_load(f)

    device = None
    for d in inventory["devices"]:
        if d["name"] == device_name:
            device = d
            break

    if device is None:
        raise ValueError(f"Équipement '{device_name}' introuvable dans devices.yaml")

    username = os.environ.get("NET_USER")
    password = os.environ.get("NET_PASS")
    if not username or not password:
        raise EnvironmentError("Variables NET_USER / NET_PASS manquantes")

    # "ios" pour Cisco IOS classique — NAPALM a un driver différent par plateforme
    driver = get_network_driver("ios")
    connection = driver(hostname=device["host"], username=username, password=password)

    connection.open()
    facts = connection.get_facts()
    connection.close()

    return facts


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_facts.py <nom_equipement>")
        sys.exit(1)

    facts = get_facts(sys.argv[1])

    # facts est un dict Python normal, directement exploitable
    print(f"Hostname : {facts['hostname']}")
    print(f"Modèle   : {facts['model']}")
    print(f"Uptime   : {facts['uptime']} secondes")
    print(f"Version OS : {facts['os_version']}")
