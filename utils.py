import random
import string
import re
from urllib.parse import urlparse


# Base62 character set
BASE62_CHARS = string.ascii_letters + string.digits  # a-zA-Z0-9


def generate_short_code(length=6):
    """Generate a random Base62 short code."""
    return ''.join(random.choices(BASE62_CHARS, k=length))


def is_valid_url(url):
    """Validate that a string is a proper URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except (ValueError, AttributeError):
        return False


def normalize_url(url):
    """Add https:// if no scheme is provided."""
    url = url.strip()
    if not url:
        return url
    if not re.match(r'^https?://', url, re.IGNORECASE):
        url = 'https://' + url
    return url


def is_valid_custom_code(code):
    """
    Validate a custom short code.
    Rules: 3-30 chars, alphanumeric + hyphens only, no leading/trailing hyphens.
    """
    if not code or len(code) < 3 or len(code) > 30:
        return False
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', code):
        return False
    return True
