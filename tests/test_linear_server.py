import html
import importlib
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode

from src import shortener
from src.hash_table import HashTable
from src.linear_probing_table import LinearProbingTable
from src.server import ShortenerHandler


class LinearProbingServerTests(unittest.TestCase):
    def setUp(self):
        importlib.reload(shortener)
        shortener.configure_table("linear")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ShortenerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.connection = HTTPConnection("127.0.0.1", self.server.server_port)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def _post_url(self, url):
        body = urlencode((("url", url),))
        self.connection.request(
            "POST",
            "/shorten",
            body,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self.connection.getresponse()
        response.read()

    def test_linear_table_displays_probe_distance_and_horner_steps(self):
        table = shortener._URL_TO_CODE
        self.assertIsInstance(table, LinearProbingTable)
        home_index = table.capacity - 1
        colliding_urls = []
        for index in range(10000):
            url = f"https://example.com/{index}"
            steps = table.hash_steps(url)
            if steps[-1][2] == home_index:
                colliding_urls.append(url)
                if len(colliding_urls) == 2:
                    break

        self.assertEqual(len(colliding_urls), 2)
        for url in colliding_urls:
            self._post_url(url)

        self.connection.request("GET", "/table")
        response = self.connection.getresponse()
        body = html.unescape(response.read().decode("utf-8"))

        self.assertEqual(response.status, 200)
        self.assertIn("Slot 0", body)
        self.assertIn("Home slot: 63", body)
        self.assertIn("Slots inspected from home: 2", body)
        self.assertIn("displacement: 1", body)
        self.assertIn("Horner hash calculation", body)
        self.assertIn("ord('h')", body)
        self.assertIn("Short link:", body)

    def test_configure_table_keeps_chaining_as_default(self):
        importlib.reload(shortener)

        self.assertIsInstance(shortener._URL_TO_CODE, HashTable)
        self.assertIsInstance(shortener._CODE_TO_URL, HashTable)


if __name__ == "__main__":
    unittest.main()
