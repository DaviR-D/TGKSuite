from urllib.parse import urlparse, urljoin
import requests
from url_tree_handler import index_nodes_by_url
from http_client import check_domain, safe_get, OutOfScopeError
from extractor import extract_links
from utils import sanitize

# Fetching these can't reveal new links, so they stay in the tree without being requested
STATIC_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg", ".woff", ".woff2", ".ttf", ".otf", ".eot",
                     ".mp3", ".mp4", ".webm", ".avi", ".mov", ".pdf", ".zip", ".gz", ".tar", ".rar", ".7z", ".exe", ".dmg", ".iso")

def normalize_link(link, base_url):
    try:
        parsed = urlparse(urljoin(base_url, link))
    except ValueError:
        return None, []

    if parsed.scheme not in ("http", "https"):
        return None, []

    child_url = parsed._replace(query="", fragment="").geturl().rstrip("/")
    query_params = [param for param in parsed.query.split("&") if param]

    return child_url, query_params

def merge_params(node, params):
    node['params'] = list(set(node['params']) | set(params))

def crawl(url, cookies, url_tree, domains=[], headers=None):
    print("\n---------------------Root URL:---------------------")
    print(sanitize(text=url))
    print("---------------------------------------------------\n")

    try:
        response = safe_get(url=url, domains=domains, cookies=cookies, headers=headers)
    except OutOfScopeError as error:
        print(f"{error}, continuing to the next...")
        return None
    except requests.exceptions.RequestException as error:
        print(f"Request to {sanitize(text=url)} failed ({type(error).__name__}), continuing to the next...")
        return None

    base_url, links = extract_links(text=response.text, content_type=response.headers.get("Content-Type", ""))

    # Relative links resolve against <base href> or the final URL after redirects
    base_url = urljoin(response.url, base_url) if base_url else response.url

    known_nodes = index_nodes_by_url(node=url_tree)
    child_nodes = dict()

    for link in links:
        # An empty link (e.g. a form without action) points to the page itself, not to <base href>
        link_base_url = base_url if link["url"] else response.url
        child_url, query_params = normalize_link(link=link["url"], base_url=link_base_url)

        if child_url is None or not check_domain(url=child_url, domains=domains):
            continue

        query_params.extend(link["params"])

        existing_node = child_nodes.get(child_url) or known_nodes.get(child_url)

        if existing_node is not None:
            merge_params(node=existing_node, params=query_params)
            continue

        child_nodes[child_url] = {"url": child_url, "params": list(set(query_params))}

    for child_node in child_nodes.values():
        print(f"\nURL found: {sanitize(text=child_node['url'])}")

        if(child_node['params']):
            print(f"Params: {sanitize(text=child_node['params'])}")

    return list(child_nodes.values())

def crawl_one(node, cookies, url_tree, domains=[], headers=None):
    if urlparse(node["url"]).path.lower().endswith(STATIC_EXTENSIONS):
        node.setdefault("childs", [])
        return

    child_nodes = crawl(url=node["url"], cookies=cookies, url_tree=url_tree, domains=domains, headers=headers)

    # Failed requests leave the node uncrawled so the next pass retries it
    if child_nodes is not None:
        node.setdefault("childs", []).extend(child_nodes)

def crawl_all(node, cookies, url_tree, domains=[], visited=None, headers=None):

    if visited is None:
        visited = set()

    if(node['url'] in visited):
        return

    visited.add(node['url'])

    # Nodes with a "childs" key were already crawled, only their children are visited
    if("childs" in node):
        for child_node in list(node["childs"]):
            crawl_all(node=child_node, cookies=cookies, url_tree=url_tree, domains=domains, visited=visited, headers=headers)
    else:
        crawl_one(node=node, cookies=cookies, url_tree=url_tree, domains=domains, headers=headers)

def deep_crawl(depth, cookies, url_tree, domains=[], headers=None):
    for i in range(0, depth):
        crawl_all(node=url_tree, cookies=cookies, url_tree=url_tree, domains=domains, headers=headers)
