import argparse
import json
import fuzzer
import crawler

url_tree = dict()
fuzzing_wordlist = ""
cookies = dict()

def add_args():
    parser = argparse.ArgumentParser(description="ShingekiSuite")
    parser.add_argument("-u", "--url", help="Target URL")
    parser.add_argument("-is", "--import-session", help="Import previous session")
    parser.add_argument("-fw", "--fuzzer-wordlist", help="Set fixed fuzzing wordlist")
    parser.add_argument("-c", "--cookie", help="Cookie (key=value)", action="append")
    args = parser.parse_args()

    return args

def load_args():
    global fuzzing_wordlist
    global url_tree

    args = add_args()

    for cookie in args.cookie or []:
        key, value = cookie.split('=', 1)
        cookies[key] = value

    url_tree["url"] = args.url

    fuzzing_wordlist = args.fuzzer_wordlist

    if(args.import_session):
        import_url_tree(args.import_session)


def main():
    methods = [print, fuzzing, craw_one, print_url_tree, print_params, print_urls_params, crawl_all, save_url_tree, import_url_tree]

    load_args()

    option = 99

    while option != "0":
        print_menu()

        option = input("Choice: ")


        methods[int(option)]()
            

def print_menu():

    print("1) Fuzz")
    print("2) Crawl")
    print("3) Show available URLs")
    print("4) Print params")
    print("5) Print URLs and params")
    print("6) Crawl all URLs")
    print("7) Export URL tree")
    print("8) Import URL tree")
    print("0) Exit")

def fuzzing():
    global fuzzing_wordlist
    global cookies
    
    target_url = search_tree(input("Target URL: "), url_tree)

    if(not fuzzing_wordlist or len(fuzzing_wordlist) == 0):
        fuzzing_wordlist = input("Wordlist: ")
        
    fuzzer.fuzz(target_url["url"], fuzzing_wordlist, cookies)

def craw_one():
    global cookies

    target_url = search_tree(input("Target URL: "), url_tree)
    target_url["childs"] = crawler.crawl(target_url["url"], cookies)

def crawl_all(node=url_tree):
    global cookies

    if("childs" in node):
        for child_node in node["childs"]:
            crawl_all(child_node)
    else:
        node["childs"] = crawler.crawl(node["url"], cookies)

def print_url_tree(current_node=url_tree, node_number="1", identation = "", include_params=False):
    print(f"{identation}{node_number}. {current_node["url"]}")

    if(include_params):
        print_params(current_node, identation=identation)

    print()

    if("childs" in current_node):
        for child_node, index in zip(current_node["childs"], range(0, len(current_node["childs"]))):
            print_url_tree(child_node, f"{node_number}.{index+1}", f"{identation}  ", include_params=include_params)

def print_params(target_url=False, identation=""):
    if(not target_url):
        target_url = search_tree(input("Target URL: "), url_tree)

    if("params" in target_url):    
        for param in target_url["params"]:
            print(f"{identation} {param}")

def print_urls_params():
    print_url_tree(include_params=True)

def search_tree(number, node):
    index_array = number.split(".")
    index_array.pop(0)
    
    if(len(index_array) == 0):
        return node
    
    else:
        next_index = int(index_array[0]) - 1
        next_node = node["childs"][next_index]

        return search_tree(".".join(index_array), next_node)
    
def save_url_tree():
    with open("output/url_tree.json", "w+", encoding="utf-8") as output:
        json.dump(url_tree, output, ensure_ascii=False, indent=2)

    print("Written in output/url_tree.json")

def import_url_tree(import_file=None):
    if(not import_file):
        import_file = input("File to import: ")

    with open(import_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    url_tree.clear()
    url_tree.update(data)
        
if __name__ == "__main__":
    main()