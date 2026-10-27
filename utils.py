import hashlib
import re

MAX_FILENAME_LENGTH = 200

def sanitize(text):
    # Escape non-printable characters so hostile content can't inject terminal escape sequences
    return ''.join(char if char.isprintable() else char.encode("unicode_escape").decode("ascii") for char in str(text))

def safe_filename(name, extension=""):
    # The hash keeps names unique, since different URLs can sanitize to the same text
    name_hash = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    sanitized_name = re.sub(r'[^a-zA-Z0-9_.-]', '-', name)[:MAX_FILENAME_LENGTH - len(name_hash) - len(extension) - 1]

    return f"{sanitized_name}-{name_hash}{extension}"
