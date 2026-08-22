"""
test_deploy_config.py — Valide deploy_config.py sans équipement réel,
y compris le cas où un device échoue sans bloquer les autres.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from netmiko.exceptions import NetmikoTimeoutException

from deploy_config import deploy_to_all, deploy_to_device, read_config_lines

FAKE_DEVICES = [
    {"name": "R-HQ", "host": "10.10.99.2", "device_type": "cisco_ios"},
    {"name": "R-Branch1", "host": "10.0.12.2", "device_type": "cisco_ios"},
]


class TestDeployToDevice(unittest.TestCase):
    @patch.dict(os.environ, {"NET_USER": "admin", "NET_PASS": "secret"})
    @patch("deploy_config.ConnectHandler")
    def test_deploy_success(self, mock_connect_handler, tmp_path=None):
        mock_connection = MagicMock()
        mock_connection.send_command.return_value = "hostname R-HQ\n..."
        mock_connect_handler.return_value = mock_connection

        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            from pathlib import Path
            ok = deploy_to_device(FAKE_DEVICES[0], ["hostname R-HQ"], Path(tmp))

            self.assertTrue(ok)
            mock_connection.send_config_set.assert_called_once_with(["hostname R-HQ"])
            mock_connection.save_config.assert_called_once()
            saved_file = Path(tmp) / "hq" / "R-HQ.cfg"
            self.assertTrue(saved_file.exists())

    @patch.dict(os.environ, {"NET_USER": "admin", "NET_PASS": "secret"})
    @patch("deploy_config.ConnectHandler")
    def test_deploy_timeout_returns_false_not_exception(self, mock_connect_handler):
        mock_connect_handler.side_effect = NetmikoTimeoutException("unreachable")

        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            ok = deploy_to_device(FAKE_DEVICES[0], ["hostname R-HQ"], Path(tmp))
            self.assertFalse(ok)  # ne lève pas d'exception, retourne juste False


class TestDeployToAll(unittest.TestCase):
    @patch.dict(os.environ, {"NET_USER": "admin", "NET_PASS": "secret"})
    @patch("deploy_config.load_inventory", return_value=FAKE_DEVICES)
    @patch("deploy_config.read_config_lines", return_value=["hostname TEST"])
    @patch("deploy_config.ConnectHandler")
    def test_one_device_failing_does_not_block_others(
        self, mock_connect_handler, mock_config, mock_inventory
    ):
        """R-HQ réussit, R-Branch1 échoue (timeout) — les deux doivent être traités."""

        def side_effect(**kwargs):
            if kwargs.get("host") == "10.0.12.2":  # R-Branch1
                raise NetmikoTimeoutException("unreachable")
            mock_conn = MagicMock()
            mock_conn.send_command.return_value = "fake running-config"
            return mock_conn

        mock_connect_handler.side_effect = side_effect

        results = deploy_to_all("fake_config.txt", output_dir="/tmp/test_configs_out")

        self.assertTrue(results["R-HQ"])
        self.assertFalse(results["R-Branch1"])
        self.assertEqual(len(results), 2)  # les deux devices ont bien été tentés


if __name__ == "__main__":
    unittest.main()
