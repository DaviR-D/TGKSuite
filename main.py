from session import *
from visual import *
from crawler import *
from fuzzer import *
from url_tree_handler import *
from get_scripts import filter_scripts
from urllib.parse import urlparse
import argparse
import re



url_tree = dict()
fuzzing_wordlist = ""
cookies = dict()
headers = dict()
domains = list()

def add_args():
    parser = argparse.ArgumentParser(description="TeigekiSuite")
    parser.add_argument("-u", "--url", help="Target domain, e.g. example.com (crawled over https and used as the default scope)", metavar="domain")
    parser.add_argument("-is", "--import-session", help="Import previous session", metavar="session")
    parser.add_argument("-fw", "--fuzzer-wordlist", help="Set fixed fuzzing wordlist", metavar="wordlist")
    parser.add_argument("-d", "--domain", help="Additional in-scope domain (multiple uses supported)", action="append", metavar="domain")
    parser.add_argument("-c", "--cookie", help="Cookie (key=value)", action="append", metavar="cookie")
    parser.add_argument("-H", "--header", help="Custom HTTP header (\"Name: Value\", multiple uses supported)", action="append", metavar="header")
    parser.add_argument("-a", "--auto-recon", help="Perform deafult automatic recon", action="store_true")
    args = parser.parse_args()

    return args

def parse_target_domain(target):
    target = target.strip().lower().rstrip(".")

    if not re.fullmatch(r'[a-z0-9.-]+(:[0-9]{1,5})?', target):
        print(f"Invalid target domain (expected e.g. example.com): {target}")
        exit(1)

    return target

def load_args():
    global fuzzing_wordlist
    global url_tree
    global domains

    args = add_args()

    for cookie in args.cookie or []:
        key, value = cookie.split('=', 1)
        cookies[key] = value

    for header in args.header or []:
        if ':' not in header:
            print(f"Invalid header (expected \"Name: Value\"): {header}")
            exit(1)
        key, value = header.split(':', 1)
        headers[key.strip()] = value.strip()

    if(args.url):
        url_tree["url"] = f"https://{parse_target_domain(target=args.url)}"
        url_tree['params'] = list()

    fuzzing_wordlist = args.fuzzer_wordlist

    if(args.import_session):
        import_session(url_tree=url_tree, import_file=args.import_session)

    if(not url_tree.get("url")):
        print("A target is required: use -u <domain> or -is <session>")
        exit(1)

    # The target domain is always in scope, -d adds extra domains
    domains = [urlparse(url_tree["url"]).hostname]
    domains.extend(domain.strip().lower().rstrip(".") for domain in args.domain or [])

    if(args.auto_recon):
        auto_recon()
        return '0'

    return 0

def handle_option(option):
    global url_tree
    global fuzzing_wordlist
    global cookies
    global headers

    handle = {
    0: lambda: print(),
    1: lambda: fuzzing(target_url=find_node_by_number(number=input("Target URL: "), node=url_tree), fuzzing_wordlist=fuzzing_wordlist, cookies=cookies, domains=domains, headers=headers),
    2: lambda: crawl_one(node=find_node_by_number(number=input("Target URL: "), node=url_tree), cookies=cookies, url_tree=url_tree, domains=domains, headers=headers),
    3: lambda: print_url_tree(current_node=url_tree),
    4: lambda: print_params(target_url=find_node_by_number(number=input("Target URL: "), node=url_tree)),
    5: lambda: print_url_tree(current_node=url_tree, include_params=True),
    6: lambda: crawl_all(node=url_tree, cookies=cookies, url_tree=url_tree, domains=domains, headers=headers),
    7: lambda: deep_crawl(depth=int(input("Depth: ")), cookies=cookies, url_tree=url_tree, domains=domains, headers=headers),
    8: lambda: filter_scripts(node=url_tree, domains=domains, cookies=cookies, headers=headers),
    9: lambda: export_session(url_tree=url_tree),
    10: lambda: import_session(url_tree=url_tree),
}
    
    handle[int(option)]()

def auto_recon():
    deep_crawl(depth=3, cookies=cookies, url_tree=url_tree, domains=domains, headers=headers)
    filter_scripts(node=url_tree, domains=domains, cookies=cookies, headers=headers)
    print("\n\nAll javascript code saved in output/scripts.js")
    export_session(url_tree=url_tree)

def main():
    option = load_args()

    while option != "0":
        print_menu()

        option = input("Choice: ")

        print()

        handle_option(option=option)


if __name__ == "__main__":
    main()