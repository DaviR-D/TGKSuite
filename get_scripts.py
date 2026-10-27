import requests
from http_client import safe_get, OutOfScopeError
from utils import sanitize, safe_filename

def filter_scripts(node, domains, cookies=None, headers=None):
    if(node['url'].endswith(".js")):
        save_script(url=node['url'], domains=domains, cookies=cookies, headers=headers)
    
    if("childs" in node):
        for child_node in node["childs"]:
            filter_scripts(node=child_node, domains=domains, cookies=cookies, headers=headers)

def save_script(url, domains, cookies=None, headers=None):
    try:
        response = safe_get(url=url, domains=domains, cookies=cookies, headers=headers, timeout=10)
        response.raise_for_status()
    except (OutOfScopeError, requests.exceptions.RequestException):
        print(f"Error while downloading {sanitize(text=url)}")
        return

    if response.status_code == 200:
        formatted_url = safe_filename(name=url.removesuffix(".js"), extension=".js")
        print(sanitize(text=url))
        with open(f"output/{formatted_url}", "w", encoding="utf-8") as f:
            f.write(f"//{url}\n\n" + response.text)
