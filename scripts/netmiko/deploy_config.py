"""
deploy_config.py — Pousse une configuration à plusieurs équipements et
sauvegarde leur running-config.

Usage :
    NET_USER=admin NET_PASS=secret python deploy_config.py config_snippet.txt

Packet Tracer limitation :
    Comme connect.py, ce script cible du vrai Cisco IOS. Voir
    tests/test_deploy_config.py pour la validation via mock.
"""

import logging
import os
import sys
from pathlib import Path

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)

from connect import build_connection_params, load_inventory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Mapping site -> nom de dossier dans configs/ (basé sur le préfixe du nom d'équipement)
SITE_FOLDER_MAP = {
    "R-HQ": "hq",
    "SW-HQ-CORE": "hq",
    "SW-HQ-ACCESS": "hq",
    "R-Branch1": "branch1",
    "SW-Branch1": "branch1",
    "R-Branch2": "branch2",
    "SW-Branch2": "branch2",
}


def read_config_lines(path: str) -> list[str]:
    """Lit un fichier texte contenant les commandes de config, une par ligne."""
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def deploy_to_device(device: dict, config_lines: list[str], output_dir: Path) -> bool:
    """
    Déploie la config sur un équipement et sauvegarde son running-config.
    Retourne True en cas de succès, False en cas d'échec (n'interrompt jamais l'appelant).
    """
    name = device["name"]
    try:
        conn_params = build_connection_params(device)
        connection = ConnectHandler(**conn_params)
    except NetmikoAuthenticationException:
        logger.error("[%s] Authentification refusée", name)
        return False
    except NetmikoTimeoutException:
        logger.error("[%s] Timeout — équipement injoignable", name)
        return False
    except Exception as exc:
        logger.error("[%s] Erreur de connexion inattendue : %s", name, exc)
        return False

    try:
        logger.info("[%s] Envoi de %d ligne(s) de configuration...", name, len(config_lines))
        connection.send_config_set(config_lines)
        connection.save_config()

        running_config = connection.send_command("show running-config")

        site_folder = SITE_FOLDER_MAP.get(name, "misc")
        target_dir = output_dir / site_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        config_path = target_dir / f"{name}.cfg"
        config_path.write_text(running_config, encoding="utf-8")

        logger.info("[%s] Config déployée et sauvegardée -> %s", name, config_path)
        return True
    except Exception as exc:
        logger.error("[%s] Échec pendant le déploiement : %s", name, exc)
        return False
    finally:
        connection.disconnect()


def deploy_to_all(config_path: str, inventory_path: str = "devices.yaml",
                   output_dir: str = "../../configs") -> dict:
    """
    Déploie la config à tous les équipements de l'inventaire.
    Retourne un résumé {device_name: bool_success}.
    """
    config_lines = read_config_lines(config_path)
    devices = load_inventory(inventory_path)
    output_path = Path(output_dir)

    results = {}
    for device in devices:
        results[device["name"]] = deploy_to_device(device, config_lines, output_path)

    return results


def print_summary(results: dict) -> None:
    succeeded = [name for name, ok in results.items() if ok]
    failed = [name for name, ok in results.items() if not ok]

    logger.info("=== Résumé du déploiement ===")
    logger.info("Réussis (%d) : %s", len(succeeded), ", ".join(succeeded) or "-")
    logger.info("Échecs (%d) : %s", len(failed), ", ".join(failed) or "-")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python deploy_config.py <fichier_config.txt>")
        sys.exit(1)

    results = deploy_to_all(sys.argv[1])
    print_summary(results)

    if any(not ok for ok in results.values()):
        sys.exit(1)
