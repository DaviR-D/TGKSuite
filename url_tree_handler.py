def find_node_by_number(number, node):
    index_array = number.split(".")
    index_array.pop(0)
    
    if(len(index_array) == 0):
        return node
    
    else:
        next_index = int(index_array[0]) - 1
        next_node = node["childs"][next_index]

        return find_node_by_number(number=".".join(index_array), node=next_node)
    
def find_node_by_url(url, node):
    if(node['url'] == url):
        return node
    
    if("childs" in node):
        for child_node in node["childs"]:
            result = find_node_by_url(url=url, node=child_node)
            if result is not None:
                return result
        
    return None