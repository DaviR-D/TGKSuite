from urllib.parse import urlparse, urljoin
import requests
from extractor import extract_links
from http_client import check_domain, safe_get, OutOfScopeError
from url_tree import index_nodes_by_url, new_node
from utils import sanitize

# Fetching these can't reveal new links, so they stay in the tree without being requested
STATIC_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg", ".woff", ".woff2", ".ttf", ".otf", ".eot",
                     ".mp3", ".mp4", ".webm", ".avi", ".mov", ".pdf", ".zip", ".gz", ".tar", ".rar", ".7z", ".exe", ".dmg", ".iso")

DEFAULT_PORTS = {"http": 80, "https": 443}

def is_static_asset(url):
    return urlparse(url).path.lower().endswith(STATIC_EXTENSIONS)

def normalize_link(link, base_url):
    """Resolves a link into an absolute URL without query or fragment, plus its query params.
    Returns (None, []) for links that aren't valid http(s) URLs."""
    try:
        parsed = urlparse(urljoin(base_url, link))

        # Backslash URLs are ambiguous between parsers, rebuilding them would silently change their host
        if parsed.scheme not in DEFAULT_PORTS or not parsed.hostname or "\\" in parsed.netloc:
            return None, []

        # Hosts are case insensitive and default ports are implicit, so both are normalized to avoid duplicates
        netloc = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
        if parsed.port is not None and parsed.port != DEFAULT_PORTS[parsed.scheme]:
            netloc = f"{netloc}:{parsed.port}"
    except ValueError:
        return None, []

    url = parsed._replace(netloc=netloc, query="", fragment="").geturl().rstrip("/")
    query_params = [param for param in parsed.query.split("&") if param]

    return url, query_params

def merge_params(node, params):
    node["params"] = list(set(node["params"]) | set(params))

def fetch_page(url, scan):
    """Returns the response, or None when the request failed or was blocked."""
    try:
        return safe_get(url=url, scan=scan)
    except OutOfScopeError as error:
        print(f"{error}, continuing to the next...")
    except requests.exceptions.RequestException as error:
        print(f"Request to {sanitize(text=url)} failed ({type(error).__name__}), continuing to the next...")

    return None

def collect_child_nodes(response, scan):
    """Builds nodes for the in-scope links never seen before. Params of already known URLs are merged into their nodes."""
    base_url, links = extract_links(text=response.text, content_type=response.headers.get("Content-Type", ""))

    # Relative links resolve against <base href> or the final URL after redirects
    base_url = urljoin(response.url, base_url) if base_url else response.url

    known_nodes = index_nodes_by_url(node=scan.url_tree)
    child_nodes = dict()

    for link in links:
        # An empty link (e.g. a form without action) points to the page itself, not to <base href>
        link_base_url = base_url if link["url"] else response.url
        url, query_params = normalize_link(link=link["url"], base_url=link_base_url)

        if url is None or not check_domain(url=url, domains=scan.domains):
            continue

        params = query_params + link["params"]
        existing_node = child_nodes.get(url, known_nodes.get(url))

        if existing_node is not None:
            merge_params(node=existing_node, params=params)
        else:
            child_nodes[url] = new_node(url=url, params=params)

    return list(child_nodes.values())

def print_found_nodes(nodes):
    for node in nodes:
        print(f"\nURL found: {sanitize(text=node['url'])}")

        if node["params"]:
            print(f"Params: {sanitize(text=node['params'])}")

def crawl(url, scan):
    """Requests a URL and returns the new child nodes found in it, or None when the request failed."""
    print("\n---------------------Root URL:---------------------")
    print(sanitize(text=url))
    print("---------------------------------------------------\n")

    response = fetch_page(url=url, scan=scan)

    if response is None:
        return None

    child_nodes = collect_child_nodes(response=response, scan=scan)
    print_found_nodes(nodes=child_nodes)

    return child_nodes

def crawl_one(node, scan):
    """Crawls a node and adds its new children. Static assets are marked as crawled without being requested."""
    if is_static_asset(url=node["url"]):
        node.setdefault("children", [])
        return

    child_nodes = crawl(url=node["url"], scan=scan)

    # Failed requests leave the node uncrawled so the next pass retries it
    if child_nodes is not None:
        node.setdefault("children", []).extend(child_nodes)

def crawl_all(node, scan, visited=None):
    """Crawls every node of the tree not crawled yet, advancing it by one level."""
    if visited is None:
        visited = set()

    if node["url"] in visited:
        return

    visited.add(node["url"])

    if "children" in node:
        for child_node in list(node["children"]):
            crawl_all(node=child_node, scan=scan, visited=visited)
    else:
        crawl_one(node=node, scan=scan)

def deep_crawl(depth, scan):
    for _ in range(depth):
        crawl_all(node=scan.url_tree, scan=scan)
