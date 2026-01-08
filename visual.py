def print_menu():

    print()
    print("1) Fuzz")
    print("2) Crawl")
    print("3) Show available URLs")
    print("4) Print params")
    print("5) Print URLs and params")
    print("6) Crawl all URLs")
    print("7) Save scripts")
    print("8) Export URL tree")
    print("9) Import URL tree")
    print("0) Exit")
    print()

def print_url_tree(current_node, node_number="1", identation = "", include_params=False):
    print(f"{identation}{node_number}. {current_node["url"]}")

    if(include_params):
        print_params(current_node, identation=identation)

    print()

    if("childs" in current_node):
        for child_node, index in zip(current_node["childs"], range(0, len(current_node["childs"]))):
            print_url_tree(child_node, f"{node_number}.{index+1}", f"{identation}  ", include_params=include_params)

def print_params(target_url=False, identation=""):
    if("params" in target_url):    
        for param in target_url["params"]:
            print(f"{identation} {param}")