import hashlib
import re

MAX_FILENAME_LENGTH = 200

def sanitize(text):
    # Escape non-printable characters so hostile content can't inject terminal escape sequences
    return ''.join(char if char.isprintable() else char.encode("unicode_escape").decode("ascii") for char in str(text))

def safe_filename(name):
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '-', name)

    if len(filename) > MAX_FILENAME_LENGTH:
        name_hash = hashlib.sha1(name.encode("utf-8")).hexdigest()[:16]
        filename = f"{filename[:MAX_FILENAME_LENGTH - 17]}-{name_hash}"

    return filename
