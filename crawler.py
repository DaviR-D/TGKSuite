from urllib.parse import urlparse, urljoin
import requests
import re
from url_tree_handler import find_node_by_url
from http_client import check_domain, safe_get, OutOfScopeError
from utils import sanitize

def crawl(url, cookies, url_tree, domains=[], headers=None):
    child_urls = list()
    print("\n---------------------Root URL:---------------------")
    print(sanitize(text=url))
    print("---------------------------------------------------\n")

    try:
        response = safe_get(url=url, domains=domains, cookies=cookies, headers=headers)
    except OutOfScopeError as error:
        print(f"{error}, continuing to the next...")
        return child_urls
    except requests.exceptions.RequestException as error:
        print(f"Request to {sanitize(text=url)} failed ({type(error).__name__}), continuing to the next...")
        return child_urls


    page_links = re.findall(r'(?:href|src)="(.*?)"', response.text)

    page_links = list(set(page_links))

    for link in page_links:
        split_url = link.strip().split("?", 1)

        child_url = split_url[0]

        child_url = child_url.rstrip("/")

        query_params = split_url[1].split("&") if len(split_url) > 1 else []

        try:
            parsed = urlparse(child_url)

            if parsed.scheme not in ("http", "https", ""):
                continue

            # Relative links resolve against the final URL after redirects
            if not parsed.scheme:
                child_url = urljoin(response.url, child_url)
        except ValueError:
            continue


        if not check_valid_url(new_url=child_url,
                               new_nodes=child_urls,
                               domains=domains,
                               url_tree=url_tree,
                               query_params=query_params
                            ):
            continue

        print(f"\nURL found: {sanitize(text=child_url)}")

        if(len(query_params) > 1):
            print(f"Params: {sanitize(text=query_params)}")


        child_urls.append({"url":child_url, "params":query_params})


    return child_urls

def crawl_one(node, cookies, url_tree, domains=[], headers=None):
    node["childs"] = crawl(url=node["url"], cookies=cookies, url_tree=url_tree, domains=domains, headers=headers)

def crawl_all(node, cookies, url_tree, domains=[], visited=None, headers=None):

    if visited is None:
        visited = set()

    if(node['url'] in visited):
        return
    
    visited.add(node['url'].rstrip("/"))

    if("childs" in node and len(node['childs']) > 0):
        for child_node in node["childs"]:
            crawl_all(node=child_node, cookies=cookies, url_tree=url_tree, domains=domains, visited=visited, headers=headers)
    else:
        crawl_one(node=node, cookies=cookies, url_tree=url_tree, domains=domains, headers=headers)

def check_valid_url(new_url, new_nodes, domains, url_tree, query_params):
    if not (check_domain(url=new_url, domains=domains)):
        return False

    for node in new_nodes:
        if(node['url'] == new_url):
            node['params'].extend(query_params)
            node['params'] = list(set(node['params']))
            return False

    existing_node = find_node_by_url(url=new_url, node=url_tree)

    if(existing_node is not None):
        existing_node['params'].extend(query_params)
        existing_node['params'] = list(set(existing_node['params']))
        return False
        
    return True

def deep_crawl(depth, cookies, url_tree, domains=[], headers=None):
    for i in range(0, depth):
        crawl_all(node=url_tree, cookies=cookies, url_tree=url_tree, domains=domains, headers=headers)
