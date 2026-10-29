from time import sleep
import os
import requests
from http_client import safe_get, OutOfScopeError
from utils import OUTPUT_DIR, safe_filename

MAX_RETRIES = 3
FUZZ_TIMEOUT = 5

def load_wordlist(file_path):
    with open(file_path, "r", encoding="utf-8") as wordlist:
        return [line for line in wordlist.read().split("\n") if line.strip()]

def request_payload(url, scan):
    """Returns the response status and elapsed seconds, or a failure label and "-"."""
    for _ in range(MAX_RETRIES):
        try:
            response = safe_get(url=url, scan=scan, timeout=FUZZ_TIMEOUT)
            return str(response.status_code), str(response.elapsed.total_seconds())
        except OutOfScopeError:
            return "OUT-OF-SCOPE", "-"
        except requests.exceptions.RequestException:
            sleep(1)

    return "ERROR", "-"

def fuzz(node, wordlist_path, scan):
    try:
        wordlist = load_wordlist(file_path=wordlist_path)
    except (OSError, UnicodeDecodeError) as error:
        print(f"Could not read wordlist {wordlist_path}: {error}")
        return

    output_path = os.path.join(OUTPUT_DIR, safe_filename(name=node["url"], extension=".txt"))

    print()

    with open(output_path, "w", encoding="utf-8") as output:
        for payload in wordlist:
            status, elapsed = request_payload(url=f"{node['url']}/{payload}/", scan=scan)
            result = f"{status} | {payload} | {elapsed}"
            output.write(result + "\n")
            print(result)

    print()
