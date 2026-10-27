# A URL tree node is {"url": str, "params": [str], "children": [node]}.
# Nodes without a "children" key haven't been crawled yet.

def new_node(url, params=None):
    return {"url": url, "params": list(set(params or []))}

def find_node_by_number(number, node):
    """Finds a node by its number in the printed tree, e.g. 1.2.1"""
    index_array = number.strip().split(".")

    if index_array[0] != "1":
        raise ValueError(f"URL number must start with 1 (e.g. 1.2.1), got {number}")

    for index in index_array[1:]:
        child_nodes = node.get("children", [])

        if not index.isdigit() or not 1 <= int(index) <= len(child_nodes):
            raise ValueError(f"URL {number} doesn't exist")

        node = child_nodes[int(index) - 1]

    return node

def index_nodes_by_url(node, index=None):
    if index is None:
        index = dict()

    index[node["url"]] = node

    for child_node in node.get("children", []):
        index_nodes_by_url(node=child_node, index=index)

    return index
