import html
import importlib
import threading
import unittest
from http.client import HTTPConnection
from urllib.parse import urlencode
from http.server import ThreadingHTTPServer

from src import shortener
from src.server import ShortenerHandler


class ShortenerServerTests(unittest.TestCase):
    def setUp(self):
        importlib.reload(shortener)
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
        return self.connection.getresponse()

    def test_home_page_has_responsive_url_form(self):
        self.connection.request("GET", "/")
        response = self.connection.getresponse()
        body = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertIn('name="url"', body)
        self.assertIn('name="viewport"', body)
        self.assertIn('action="/shorten"', body)

    def test_shortening_shows_link_and_opening_it_redirects(self):
        url = "https://example.com/original"

        response = self._post_url(url)
        result = response.read().decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertIn('href="/0"', result)
        self.assertIn(f"http://127.0.0.1:{self.server.server_port}/0", result)

        self.connection.request("GET", "/0")
        redirect = self.connection.getresponse()
        redirect.read()
        self.assertEqual(redirect.status, 302)
        self.assertEqual(redirect.getheader("Location"), url)

    def test_invalid_url_returns_bad_request_and_unknown_code_is_not_found(self):
        response = self._post_url("ftp://example.com/file")
        response.read()
        self.assertEqual(response.status, 400)

        self.connection.request("GET", "/missing")
        response = self.connection.getresponse()
        response.read()
        self.assertEqual(response.status, 404)

    def test_table_shows_chained_nodes_and_expandable_horner_steps(self):
        self._post_url("https://example.com/a").read()
        self._post_url("https://example.com/i").read()

        self.connection.request("GET", "/table")
        response = self.connection.getresponse()
        body = html.unescape(response.read().decode("utf-8"))

        self.assertEqual(response.status, 200)
        self.assertIn("Bucket ", body)
        self.assertIn("URL key:", body)
        self.assertIn("Short code:", body)
        self.assertIn("Short link:", body)
        self.assertIn("→", body)
        self.assertGreaterEqual(body.count("<details>"), 2)
        self.assertIn("Horner hash calculation", body)
        self.assertIn("ord('a')", body)
        self.assertIn("ord('i')", body)


if __name__ == "__main__":
    unittest.main()
