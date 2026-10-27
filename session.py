import json
import os
from utils import OUTPUT_DIR

SESSION_PATH = os.path.join(OUTPUT_DIR, "url_tree.json")

def export_session(url_tree):
    with open(SESSION_PATH, "w", encoding="utf-8") as output:
        json.dump(url_tree, output, ensure_ascii=False, indent=2)

    print(f"Session written in {SESSION_PATH}")

def import_session(import_file):
    """Returns the URL tree saved in a session file."""
    with open(import_file, "r", encoding="utf-8") as file:
        url_tree = json.load(file)

    if not isinstance(url_tree, dict) or not isinstance(url_tree.get("url"), str):
        raise ValueError("not a TeigekiSuite session (missing root URL)")

    return url_tree
