import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_encode_zero(self):
        self.assertEqual(encode(0), "0")

    def test_encode_alphabet_boundaries(self):
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")

    def test_encode_and_decode_round_trip(self):
        for value in (1, 61, 62, 3844, 2**128):
            with self.subTest(value=value):
                self.assertEqual(decode(encode(value)), value)

    def test_decode_rejects_empty_or_invalid_input(self):
        for encoded in ("", "!", "0-"):
            with self.subTest(encoded=encoded):
                with self.assertRaises(ValueError):
                    decode(encoded)

    def test_encode_rejects_negative_and_non_integer_values(self):
        with self.assertRaises(ValueError):
            encode(-1)
        for value in (True, 1.5, "1"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    encode(value)


if __name__ == "__main__":
    unittest.main()
