"""
test_connect.py — Valide connect.py sans équipement réel.

Packet Tracer limitation :
    On simule ConnectHandler avec unittest.mock, car Packet Tracer ne
    peut pas être atteint par une vraie session SSH Netmiko.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connect import get_show_version


class TestGetShowVersion(unittest.TestCase):

    @patch.dict(os.environ, {"NET_USER": "admin", "NET_PASS": "secret"})
    @patch("connect.yaml.safe_load")
    @patch("connect.ConnectHandler")
    def test_get_show_version_success(self, mock_connect_handler, mock_yaml):
        # Fausse réponse de l'inventaire, pas besoin d'un vrai fichier devices.yaml
        mock_yaml.return_value = {
            "devices": [{"name": "R-HQ", "host": "10.10.99.2", "device_type": "cisco_ios"}]
        }

        # Fausse session SSH qui répond comme un vrai routeur le ferait
        mock_connection = MagicMock()
        mock_connection.send_command.return_value = "Cisco IOS Software, Version 15.2"
        mock_connect_handler.return_value = mock_connection

        with patch("builtins.open", unittest.mock.mock_open(read_data="fake yaml")):
            result = get_show_version("R-HQ")

        self.assertIn("Cisco IOS", result)
        mock_connection.send_command.assert_called_once_with("show version")
        mock_connection.disconnect.assert_called_once()

    @patch.dict(os.environ, {"NET_USER": "admin", "NET_PASS": "secret"})
    @patch("connect.yaml.safe_load")
    def test_device_not_in_inventory(self, mock_yaml):
        mock_yaml.return_value = {
            "devices": [{"name": "R-HQ", "host": "10.10.99.2", "device_type": "cisco_ios"}]
        }

        with patch("builtins.open", unittest.mock.mock_open(read_data="fake yaml")):
            with self.assertRaises(ValueError):
                get_show_version("R-Inexistant")

    @patch.dict(os.environ, {}, clear=True)
    @patch("connect.yaml.safe_load")
    def test_missing_credentials(self, mock_yaml):
        mock_yaml.return_value = {
            "devices": [{"name": "R-HQ", "host": "10.10.99.2", "device_type": "cisco_ios"}]
        }

        with patch("builtins.open", unittest.mock.mock_open(read_data="fake yaml")):
            with self.assertRaises(EnvironmentError):
                get_show_version("R-HQ")


if __name__ == "__main__":
    unittest.main()