import argparse
import fuzzer
import crawler

url_tree = dict()

def main():
    methods = [print, fuzzing, crawling, print_url_tree, print_params, print_urls_params]

    option = 99
    parser = argparse.ArgumentParser(description="ShingekiSuite")
    parser.add_argument("-u", "--url", help="Target URL")
    args = parser.parse_args()
    url_tree["url"] = args.url

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
    print("0) Exit")

def fuzzing():
    target_url = search_tree(input("Target URL: "), url_tree)
    wordlist_path = input("Wordlist: ")
    fuzzer.fuzz(target_url["url"], wordlist_path)

def crawling():
    target_url = search_tree(input("Target URL: "), url_tree)
    target_url["childs"] = crawler.crawl(target_url["url"])

def print_url_tree(current_node=url_tree, node_number="1", level=1, include_params=False):
    identation = ""

    for l in range(0, level):
        identation += "  "

    print(f"{identation}{node_number}. {current_node["url"]}")

    if(include_params):
        print_params(current_node, identation=identation)

    print()

    if("childs" in current_node):
        for child_node, index in zip(current_node["childs"], range(0, len(current_node["childs"]))):
            print_url_tree(child_node, f"{node_number}.{index+1}", level+1, include_params=include_params)

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
        

if __name__ == "__main__":
    main()