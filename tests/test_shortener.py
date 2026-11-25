import importlib
import unittest

from src import shortener


class ShortenerTests(unittest.TestCase):
    def setUp(self):
        self.shortener = importlib.reload(shortener)

    def test_first_url_receives_zero_and_duplicate_url_reuses_its_code(self):
        url = "https://example.com/page"

        code = self.shortener.shorten(url)

        self.assertEqual(code, "0")
        self.assertEqual(self.shortener.shorten(url), code)
        self.assertEqual(self.shortener.expand(code), url)

    def test_distinct_urls_receive_distinct_codes(self):
        first_url = "https://example.com/first"
        second_url = "https://example.com/second"

        first_code = self.shortener.shorten(first_url)
        second_code = self.shortener.shorten(second_url)

        self.assertNotEqual(first_code, second_code)
        self.assertEqual(self.shortener.expand(first_code), first_url)
        self.assertEqual(self.shortener.expand(second_code), second_url)

    def test_urls_differing_only_in_case_remain_distinct(self):
        lower_url = "https://example.com/Path"
        upper_url = "https://example.com/path"

        lower_code = self.shortener.shorten(lower_url)
        upper_code = self.shortener.shorten(upper_url)

        self.assertNotEqual(lower_code, upper_code)
        self.assertEqual(self.shortener.expand(lower_code), lower_url)
        self.assertEqual(self.shortener.expand(upper_code), upper_url)

    def test_codes_are_case_sensitive(self):
        urls = [f"https://example.com/{index}" for index in range(37)]
        codes = [self.shortener.shorten(url) for url in urls]

        self.assertEqual(codes[10], "a")
        self.assertEqual(codes[36], "A")
        self.assertNotEqual(codes[10], codes[36])
        self.assertEqual(self.shortener.expand("a"), urls[10])
        self.assertEqual(self.shortener.expand("A"), urls[36])

    def test_empty_and_unknown_codes_raise_key_error(self):
        for code in ("", "missing"):
            with self.subTest(code=code):
                with self.assertRaises(KeyError):
                    self.shortener.expand(code)

    def test_http_and_https_absolute_urls_are_accepted(self):
        for url in ("http://example.com/", "https://example.com/path?q=1"):
            with self.subTest(url=url):
                code = self.shortener.shorten(url)
                self.assertEqual(self.shortener.expand(code), url)

    def test_url_at_maximum_length_is_accepted(self):
        prefix = "https://example.com/"
        url = prefix + "x" * (2048 - len(prefix))

        self.assertEqual(len(url), 2048)
        code = self.shortener.shorten(url)

        self.assertEqual(self.shortener.expand(code), url)

    def test_invalid_urls_raise_value_error(self):
        invalid_urls = (
            "",
            "ftp://example.com/file",
            "https://example.com/has space",
            "https://",
            "/relative/path",
            "https://example.com/" + "x" * 2048,
            None,
            42,
        )
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    self.shortener.shorten(url)

    def test_a_new_service_state_does_not_retain_previous_urls(self):
        code = self.shortener.shorten("https://example.com/temporary")

        self.shortener = importlib.reload(self.shortener)

        with self.assertRaises(KeyError):
            self.shortener.expand(code)


if __name__ == "__main__":
    unittest.main()
