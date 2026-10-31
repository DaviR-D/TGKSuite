import os
import requests
from extractor import extract_inline_scripts
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

def save_inline_scripts(response, scan):
    """Saves the inline <script> blocks of an HTML page as .js files in the output directory.

    Each file keeps the page URL on the first line (with an #inline-N marker) so the
    static analysis can trace it back to its origin, just like downloaded .js files."""
    inline_scripts = extract_inline_scripts(text=response.text, content_type=response.headers.get("Content-Type", ""))

    for index, script in enumerate(inline_scripts, start=1):
        marker = f"{response.url}#inline-{index}"
        output_path = os.path.join(OUTPUT_DIR, safe_filename(name=marker, extension=".js"))

        with open(output_path, "w", encoding="utf-8") as script_file:
            script_file.write(f"//{marker}\n\n{script}")
