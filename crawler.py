import requests
import re

def crawl(url):
    child_urls = list()
    print()
    print("---------------------Root URL:---------------------")
    print(url)
    print("---------------------------------------------------")
    print()

    response = requests.get(url)

    hrefs = re.findall(r'href="(.*?)"', response.text)

    for ref in hrefs:
        split_url = ref.split("?")
        query_params = split_url[-1].split("&")

        print()

        print(f"------Child URL:------")
        print(split_url[0])
        print(f"----------------------")

        if(len(query_params) > 1):
            print("------Params------")
            for param in query_params:
                print(param)
            print("------------------")

        print()

        child_urls.append({"url":split_url[0], "params":query_params})


    return child_urls


