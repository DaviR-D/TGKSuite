def find_node_by_number(number, node):
    index_array = number.strip().split(".")

    if(index_array[0] != "1"):
        raise ValueError(f"URL number must start with 1 (e.g. 1.2.1), got {number}")

    for index in index_array[1:]:
        child_nodes = node.get("childs", [])

        if(not index.isdigit() or not 1 <= int(index) <= len(child_nodes)):
            raise ValueError(f"URL {number} doesn't exist")

        node = child_nodes[int(index) - 1]

    return node


def find_node_by_url(url, node):
    if(node['url'] == url):
        return node
    
    if("childs" in node):
        for child_node in node["childs"]:
            result = find_node_by_url(url=url, node=child_node)
            if result is not None:
                return result
        
    return None
def index_nodes_by_url(node, index=None):
    if index is None:
        index = dict()

    index[node['url']] = node

    for child_node in node.get("childs", []):
        index_nodes_by_url(node=child_node, index=index)

    return index
