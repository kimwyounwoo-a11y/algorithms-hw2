from contextlib import redirect_stdout
from io import StringIO
import socket
import unittest
from unittest.mock import patch

from src.server import ShortenerHandler, _create_server


class ServerStartupTests(unittest.TestCase):
    def test_occupied_port_falls_back_to_an_available_port(self):
        occupied_socket = socket.socket()
        occupied_socket.bind(("127.0.0.1", 0))
        occupied_socket.listen()
        occupied_port = occupied_socket.getsockname()[1]
        server = None
        try:
            server = _create_server(occupied_port)

            self.assertIsNotNone(server)
            self.assertNotEqual(server.server_port, occupied_port)
            self.assertIs(server.RequestHandlerClass, ShortenerHandler)
        finally:
            if server is not None:
                server.server_close()
            occupied_socket.close()

    def test_existing_url_shortener_is_not_started_twice(self):
        occupied_socket = socket.socket()
        occupied_socket.bind(("127.0.0.1", 0))
        occupied_socket.listen()
        occupied_port = occupied_socket.getsockname()[1]
        try:
            output = StringIO()
            with patch(
                "src.server._is_url_shortener_running", return_value=True
            ), redirect_stdout(output):
                server = _create_server(occupied_port)
            self.assertIsNone(server)
            self.assertIn("already running", output.getvalue())
        finally:
            occupied_socket.close()


if __name__ == "__main__":
    unittest.main()
