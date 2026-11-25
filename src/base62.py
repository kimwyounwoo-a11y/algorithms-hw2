"""Base62 conversion for non-negative integers."""

BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode(value: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("value must be an integer")
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return BASE62_ALPHABET[0]

    encoded = []
    while value:
        value, remainder = divmod(value, len(BASE62_ALPHABET))
        encoded.append(BASE62_ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode(encoded: str) -> int:
    if not isinstance(encoded, str):
        raise TypeError("encoded value must be a string")
    if not encoded:
        raise ValueError("encoded value must not be empty")

    value = 0
    for character in encoded:
        try:
            digit = BASE62_ALPHABET.index(character)
        except ValueError as error:
            raise ValueError(f"invalid base62 character: {character!r}") from error
        value = value * len(BASE62_ALPHABET) + digit
    return value
