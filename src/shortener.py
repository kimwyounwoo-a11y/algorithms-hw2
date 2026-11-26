"""In-memory URL shortening backed by custom hash tables."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable
from src.linear_probing_table import LinearProbingTable

_Table = HashTable[str] | LinearProbingTable[str]
_URL_TO_CODE: _Table = HashTable()
_CODE_TO_URL: _Table = HashTable()
_NEXT_ID = 0
_MAX_URL_LENGTH = 2048


def configure_table(table_type: str = "chaining") -> None:
    """Select the backing table implementation and reset in-memory mappings."""
    global _URL_TO_CODE, _CODE_TO_URL, _NEXT_ID

    if table_type == "chaining":
        _URL_TO_CODE = HashTable()
        _CODE_TO_URL = HashTable()
    elif table_type == "linear":
        _URL_TO_CODE = LinearProbingTable()
        _CODE_TO_URL = LinearProbingTable()
    else:
        raise ValueError("table_type must be 'chaining' or 'linear'")
    _NEXT_ID = 0


def _validate_url(url: object) -> str:
    if not isinstance(url, str):
        raise ValueError("URL must be a string")
    if not url or len(url) > _MAX_URL_LENGTH:
        raise ValueError("URL must be between 1 and 2048 characters")
    if any(character.isspace() for character in url):
        raise ValueError("URL must not contain whitespace")

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        parsed.port
    except ValueError as error:
        raise ValueError("URL is malformed") from error

    if parsed.scheme not in ("http", "https") or not parsed.netloc or not hostname:
        raise ValueError("URL must be an absolute HTTP or HTTPS URL with a host")
    return url


def shorten(url: str) -> str:
    """Return a stable base62 code for a valid absolute HTTP(S) URL."""
    global _NEXT_ID

    validated_url = _validate_url(url)
    if _URL_TO_CODE.contains(validated_url):
        return _URL_TO_CODE.get(validated_url)

    code = encode(_NEXT_ID)
    _NEXT_ID += 1
    _URL_TO_CODE.put(validated_url, code)
    _CODE_TO_URL.put(code, validated_url)
    return code


def expand(code: str) -> str:
    """Return the URL stored for a code, or raise KeyError if it is unknown."""
    return _CODE_TO_URL.get(code)
