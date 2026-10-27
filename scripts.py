import os
import requests
from http_client import safe_get, OutOfScopeError
from utils import OUTPUT_DIR, sanitize, safe_filename

SCRIPT_TIMEOUT = 10

def save_scripts(node, scan):
    """Downloads every .js URL of the tree into the output directory."""
    if node["url"].endswith(".js"):
        save_script(url=node["url"], scan=scan)

    for child_node in node.get("children", []):
        save_scripts(node=child_node, scan=scan)

def save_script(url, scan):
    try:
        response = safe_get(url=url, scan=scan, timeout=SCRIPT_TIMEOUT)
        response.raise_for_status()
    except (OutOfScopeError, requests.exceptions.RequestException):
        print(f"Error while downloading {sanitize(text=url)}")
        return

    if response.status_code != 200:
        return

    output_path = os.path.join(OUTPUT_DIR, safe_filename(name=url.removesuffix(".js"), extension=".js"))
    print(sanitize(text=url))

    with open(output_path, "w", encoding="utf-8") as script_file:
        script_file.write(f"//{url}\n\n{response.text}")
