"""
test_get_facts.py — Valide get_facts.py sans équipement réel.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, mock_open

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from get_facts import get_facts

FAKE_INVENTORY = {
    "devices": [{"name": "R-HQ", "host": "10.10.99.2", "device_type": "cisco_ios"}]
}

# Exemple de ce que NAPALM retournerait réellement pour get_facts() sur un vrai IOS
FAKE_FACTS = {
    "hostname": "R-HQ",
    "model": "Cisco 2911",
    "uptime": 3600,
    "os_version": "15.2(4)M6",
}


class TestGetFacts(unittest.TestCase):

    @patch.dict(os.environ, {"NET_USER": "admin", "NET_PASS": "secret"})
    @patch("get_facts.yaml.safe_load", return_value=FAKE_INVENTORY)
    @patch("get_facts.get_network_driver")
    def test_get_facts_returns_structured_data(self, mock_get_driver, mock_yaml):
        # Simule la connexion NAPALM et sa réponse
        mock_connection = MagicMock()
        mock_connection.get_facts.return_value = FAKE_FACTS
        mock_driver_class = MagicMock(return_value=mock_connection)
        mock_get_driver.return_value = mock_driver_class

        with patch("builtins.open", mock_open(read_data="fake yaml")):
            facts = get_facts("R-HQ")

        self.assertEqual(facts["hostname"], "R-HQ")
        self.assertEqual(facts["model"], "Cisco 2911")
        mock_connection.open.assert_called_once()
        mock_connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
