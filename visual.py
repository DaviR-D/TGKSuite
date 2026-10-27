from utils import sanitize

def print_menu(menu_options):
    print()

    for number, (label, _) in menu_options.items():
        print(f"{number}) {label}")

    print()

def print_url_tree(node, node_number="1", indentation="", include_params=False):
    print(f"{indentation}{node_number}. {sanitize(text=node['url'])}")

    if include_params:
        print_params(node=node, indentation=indentation)

    print()

    for index, child_node in enumerate(node.get("children", []), start=1):
        print_url_tree(node=child_node, node_number=f"{node_number}.{index}", indentation=f"{indentation}  ", include_params=include_params)

def print_params(node, indentation=""):
    for param in node.get("params", []):
        print(f"{indentation} {sanitize(text=param)}")
