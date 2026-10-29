from datetime import datetime
from itertools import count
from urllib.parse import urlsplit
import os
from utils import safe_filename

# Logs hold cookies and auth headers in full, so only the current user can read them
LOGS_DIR = "logs"
LOGS_DIR_MODE = 0o700
LOG_FILE_MODE = 0o600

HTTP_VERSIONS = {10: "HTTP/1.0", 11: "HTTP/1.1", 20: "HTTP/2"}

log_counter = count(1)

def create_logs_dir():
    os.makedirs(LOGS_DIR, mode=LOGS_DIR_MODE, exist_ok=True)

def format_headers(headers):
    return "".join(f"{name}: {value}\r\n" for name, value in headers)

def format_request(request):
    # urllib3 adds the Host header itself, so it isn't part of the prepared request
    host_header = [("Host", urlsplit(request.url).netloc)] if "Host" not in request.headers else []
    head = f"{request.method} {request.path_url} HTTP/1.1\r\n{format_headers(headers=host_header + list(request.headers.items()))}\r\n"
    body = request.body.encode("utf-8") if isinstance(request.body, str) else request.body or b""

    return head.encode("utf-8") + body

def format_response(response):
    http_version = HTTP_VERSIONS.get(response.raw.version, "HTTP/1.1")
    # raw headers keep repeated headers (e.g. several Set-Cookie) as separate lines
    head = f"{http_version} {response.status_code} {response.reason}\r\n{format_headers(headers=response.raw.headers.items())}\r\n"

    # The body is already decompressed, even if Content-Encoding says otherwise
    return head.encode("utf-8", errors="replace") + response.content

def log_exchange(request, response=None, error=None):
    """Saves a request and its response (or the error that prevented one) in its own file."""
    create_logs_dir()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    filename = safe_filename(name=f"{timestamp}_{next(log_counter):05d}_{request.method}_{request.url}", extension=".txt")
    sections = [b"=== REQUEST ===\r\n", format_request(request=request)]

    if response is not None:
        sections += [b"\r\n\r\n=== RESPONSE ===\r\n", format_response(response=response)]
    else:
        sections += [b"\r\n\r\n=== ERROR ===\r\n", f"{type(error).__name__}: {error}".encode("utf-8", errors="replace")]

    file_descriptor = os.open(os.path.join(LOGS_DIR, filename), os.O_WRONLY | os.O_CREAT | os.O_EXCL, LOG_FILE_MODE)

    with os.fdopen(file_descriptor, "wb") as log_file:
        log_file.write(b"".join(sections))
