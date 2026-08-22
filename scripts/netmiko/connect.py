"""
connect.py — Connexion de base à un équipement Cisco IOS via Netmiko.

Usage :
    NET_USER=admin NET_PASS=secret python connect.py R-HQ

Packet Tracer limitation :
    Ce script cible du vrai Cisco IOS (matériel réel ou Cisco DevNet
    Sandbox). Packet Tracer ne peut pas être atteint par une vraie
    session SSH Netmiko — voir tests/test_connect.py pour la
    validation avec mock.
"""

import logging
import os
import sys

import yaml
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_show_version(device_name):
    """Se connecte à l'équipement donné et retourne la sortie de 'show version'."""

    # 1. Charger l'inventaire et trouver le bon équipement
    with open("devices.yaml", "r", encoding="utf-8") as f:
        inventory = yaml.safe_load(f)

    device = None
    for d in inventory["devices"]:
        if d["name"] == device_name:
            device = d
            break

    if device is None:
        raise ValueError(f"Équipement '{device_name}' introuvable dans devices.yaml")

    # 2. Récupérer les identifiants depuis les variables d'environnement
    username = os.environ.get("NET_USER")
    password = os.environ.get("NET_PASS")

    if not username or not password:
        raise EnvironmentError("Variables NET_USER / NET_PASS manquantes")

    # 3. Se connecter
    logger.info("Connexion à %s (%s)...", device_name, device["host"])

    try:
        connection = ConnectHandler(
            device_type=device["device_type"],
            host=device["host"],
            username=username,
            password=password,
        )
    except NetmikoAuthenticationException:
        logger.error("Authentification refusée sur %s", device_name)
        raise
    except NetmikoTimeoutException:
        logger.error("%s injoignable (timeout)", device_name)
        raise

    # 4. Envoyer la commande et se déconnecter proprement
    output = connection.send_command("show version")
    connection.disconnect()

    logger.info("Commande envoyée avec succès à %s", device_name)
    return output


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python connect.py <nom_equipement>")
        sys.exit(1)

    device_name = sys.argv[1]
    result = get_show_version(device_name)
    print(result)