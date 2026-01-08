from session import *
from visual import *
from crawler import *
from fuzzer import *
from url_tree_handler import *
from get_scripts import filter_scripts
import argparse



url_tree = dict()
fuzzing_wordlist = ""
cookies = dict()
domain = ""

def add_args():
    parser = argparse.ArgumentParser(description="TeigekiSuite")
    parser.add_argument("-u", "--url", help="Target URL", metavar="url")
    parser.add_argument("-is", "--import-session", help="Import previous session", metavar="session")
    parser.add_argument("-fw", "--fuzzer-wordlist", help="Set fixed fuzzing wordlist", metavar="wordlist")
    parser.add_argument("-d", "--domain", help="Only crawl through URLs in this domain", metavar="domain")
    parser.add_argument("-c", "--cookie", help="Cookie (key=value)", action="append", metavar="cookie")
    args = parser.parse_args()

    return args

def load_args():
    global fuzzing_wordlist
    global url_tree
    global domain

    args = add_args()

    for cookie in args.cookie or []:
        key, value = cookie.split('=', 1)
        cookies[key] = value

    url_tree["url"] = args.url
    url_tree['params'] = list()

    fuzzing_wordlist = args.fuzzer_wordlist

    if(args.import_session):
        import_session(url_tree=url_tree, import_file=args.import_session)

    if(args.domain):
        domain = args.domain

def handle_option(option):
    global url_tree
    global fuzzing_wordlist
    global cookies

    handle = {
    0: lambda: print(),
    1: lambda: fuzzing(find_node_by_number(input("Target URL: "), url_tree), fuzzing_wordlist, cookies),
    2: lambda: crawl_one(find_node_by_number(input("Target URL: "), url_tree), cookies, url_tree=url_tree, domain=domain),
    3: lambda: print_url_tree(current_node=url_tree),
    4: lambda: print_params(find_node_by_number(input("Target URL: "), url_tree)),
    5: lambda: print_url_tree(current_node=url_tree, include_params=True),
    6: lambda: crawl_all(node=url_tree, cookies=cookies, url_tree=url_tree, domain=domain),
    7: lambda: filter_scripts(node=url_tree),
    8: lambda: export_session(url_tree=url_tree),
    9: lambda: import_session(url_tree),
}
    
    handle[int(option)]()


def main():
    load_args()

    option = 99

    while option != "0":
        print_menu()

        option = input("Choice: ")

        print()

        handle_option(option)


if __name__ == "__main__":
    main()