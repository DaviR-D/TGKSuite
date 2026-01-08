from urllib.parse import urlparse
import requests
import re

def crawl(url, cookies, domain=""):
    child_urls = list()
    print()
    print("---------------------Root URL:---------------------")
    print(url)
    print("---------------------------------------------------")
    print()

    response = requests.get(url, cookies=cookies)

    links = re.findall(r'(?:href|src)="(.*?)"', response.text)

    for link in links:
        split_url = link.split("?")
        child_url = split_url[0]
        if("http" not in child_url):
            child_url = url + '/' + child_url
        query_params = split_url[-1].split("&")

        print()

        if not (check_domain(url=child_url, domain=domain)):
            continue

        print(f"------Child URL:------")
        print(child_url)
        print(f"----------------------")

        if(len(query_params) > 1):
            print("------Params------")
            for param in query_params:
                print(param)
            print("------------------")

        print()

        child_urls.append({"url":child_url, "params":query_params})


    return child_urls

def crawl_one(target_url, cookies, domain=""):
    target_url["childs"] = crawl(target_url["url"], cookies, domain=domain)

def crawl_all(node, cookies):
    if("childs" in node):
        for child_node in node["childs"]:
            crawl_all(child_node, cookies)
    else:
        crawl_one(node, cookies)

def check_domain(url, domain):
    new_url_domain = urlparse(url).hostname

    return new_url_domain == domain or new_url_domain.endswith(f'.{domain}') or domain == ''

