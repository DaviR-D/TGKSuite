from urllib.parse import urlparse, urljoin
from urllib3.util import parse_url
import requests
import re
from utils import sanitize

MAX_REDIRECTS = 10
DEFAULT_TIMEOUT = 60

# Backslashes, whitespace and control characters are parsed differently by urlparse and requests
FORBIDDEN_URL_CHARS = re.compile(r'[\\\x00-\x20\x7f]')

class OutOfScopeError(Exception):
    pass

def get_url_host(url):
    """Returns the URL's host, or None when the URL is invalid, not https, or ambiguous between parsers."""
    if FORBIDDEN_URL_CHARS.search(url):
        return None

    try:
        parsed_url = urlparse(url)
        parsed_host = parsed_url.hostname
        prepared_url = requests.Request("GET", url).prepare().url
        request_host = parse_url(prepared_url).host
    except (ValueError, requests.exceptions.RequestException):
        return None

    if parsed_url.scheme != "https" or not parsed_host or not request_host:
        return None

    # Only trust the host when both parsers agree on it
    if parsed_host != request_host.lower():
        return None

    return parsed_host.rstrip(".")

def check_domain(url, domains):
    url_host = get_url_host(url=url)

    if url_host is None:
        return False

    for domain in domains:
        if url_host == domain or url_host.endswith(f".{domain}"):
            return True

    return False

def safe_get(url, scan, timeout=DEFAULT_TIMEOUT):
    """GET that follows redirects only while they stay in scope, sending the scan's cookies and headers."""
    # The session keeps cookies set by intermediate redirects (e.g. login flows)
    with requests.Session() as session:
        for _ in range(MAX_REDIRECTS + 1):
            if not check_domain(url=url, domains=scan.domains):
                raise OutOfScopeError(f"Out of scope or invalid URL blocked: {sanitize(text=url)}")

            response = session.get(url, cookies=scan.cookies, headers=scan.headers, timeout=timeout, allow_redirects=False)

            if not response.is_redirect:
                return response

            url = urljoin(response.url, response.headers["Location"])

    raise requests.exceptions.TooManyRedirects(f"Exceeded {MAX_REDIRECTS} redirects")
