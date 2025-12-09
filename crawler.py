import requests
import re

def crawl(url, cookies):
    child_urls = list()
    print()
    print("---------------------Root URL:---------------------")
    print(url)
    print("---------------------------------------------------")
    print()

    response = requests.get(url, cookies=cookies)

    hrefs = re.findall(r'href="(.*?)"', response.text)

    for ref in hrefs:
        split_url = ref.split("?")
        child_url = split_url[0]
        if("http" not in child_url):
            child_url = url + child_url
        query_params = split_url[-1].split("&")

        print()

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


