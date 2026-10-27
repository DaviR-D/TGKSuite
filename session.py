import json

def export_session(url_tree):
    with open("output/url_tree.json", "w+", encoding="utf-8") as output:
        json.dump(url_tree, output, ensure_ascii=False, indent=2)

    print("Session written in output/url_tree.json")

def import_session(url_tree, import_file):
    with open(import_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    if(not isinstance(data, dict) or not isinstance(data.get("url"), str)):
        raise ValueError("not a TeigekiSuite session (missing root URL)")

    url_tree.clear()
    url_tree.update(data)