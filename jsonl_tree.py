import json
import os
from utils import OUTPUT_DIR

JSONL_PATH = os.path.join(OUTPUT_DIR, "url_tree.jsonl")

class JsonlTreeWriter:
    """Streams the URL tree to a .jsonl file as it's built, one node per line.

    Each line is {"url": ..., "params": [...], "parent": <url or null>}, written
    and flushed the moment a node is discovered, so the file can be tailed live
    (e.g. tail -f) while -a crawls. Nodes are deduplicated by URL."""
    def __init__(self, path=JSONL_PATH):
        self.path = path
        self._file = open(path, "w", encoding="utf-8")
        self._seen = set()

    def record(self, node, parent_url=None):
        if node["url"] in self._seen:
            return

        self._seen.add(node["url"])
        line = {"url": node["url"], "params": node["params"], "parent": parent_url}

        self._file.write(json.dumps(line, ensure_ascii=False) + "\n")
        self._file.flush()

    def close(self):
        self._file.close()
