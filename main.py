from session import *
from visual import *
from crawler import *
from fuzzer import *
from url_tree_handler import *
from get_scripts import filter_scripts
from urllib.parse import urlparse
import argparse
import os
import re



url_tree = dict()
fuzzing_wordlist = ""
cookies = dict()
headers = dict()
domains = list()

def positive_int(value):
    if not value.isdigit() or int(value) < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value}")

    return int(value)

def add_args():
    parser = argparse.ArgumentParser(description="TeigekiSuite")
    parser.add_argument("-u", "--url", help="Target domain, e.g. example.com (crawled over https and used as the default scope)", metavar="domain")
    parser.add_argument("-is", "--import-session", help="Import previous session", metavar="session")
    parser.add_argument("-fw", "--fuzzer-wordlist", help="Set fixed fuzzing wordlist", metavar="wordlist")
    parser.add_argument("-d", "--domain", help="Additional in-scope domain (multiple uses supported)", action="append", metavar="domain")
    parser.add_argument("-c", "--cookie", help="Cookie (key=value)", action="append", metavar="cookie")
    parser.add_argument("-H", "--header", help="Custom HTTP header (\"Name: Value\", multiple uses supported)", action="append", metavar="header")
    parser.add_argument("-a", "--auto-recon", help="Perform deafult automatic recon", action="store_true")
    parser.add_argument("-cd", "--crawl-depth", help="Crawling depth used by the automatic recon (default: 3)", type=positive_int, default=3, metavar="depth")
    args = parser.parse_args()

    return args

def read_positive_int(prompt):
    value = input(prompt).strip()

    if not value.isdigit() or int(value) < 1:
        raise ValueError(f"expected a positive integer, got {value}")

    return int(value)

def parse_domain(domain, allow_port=False):
    domain = domain.strip().lower().rstrip(".")
    port_regex = r'(:[0-9]{1,5})?' if allow_port else ''

    if not re.fullmatch(r'[a-z0-9-]+(\.[a-z0-9-]+)*' + port_regex, domain):
        print(f"Invalid domain (expected e.g. example.com, without scheme or path{'' if allow_port else ' or port'}): {domain}")
        exit(1)

    # 443 is the https default, keeping it would duplicate URLs found without it
    return domain.removesuffix(":443")

def load_args():
    global fuzzing_wordlist
    global url_tree
    global domains

    args = add_args()

    for cookie in args.cookie or []:
        if '=' not in cookie:
            print(f"Invalid cookie (expected \"key=value\"): {cookie}")
            exit(1)
        key, value = cookie.split('=', 1)
        cookies[key] = value

    for header in args.header or []:
        if ':' not in header:
            print(f"Invalid header (expected \"Name: Value\"): {header}")
            exit(1)
        key, value = header.split(':', 1)
        headers[key.strip()] = value.strip()

    if(args.url):
        url_tree["url"] = f"https://{parse_domain(domain=args.url, allow_port=True)}"
        url_tree['params'] = list()

    fuzzing_wordlist = args.fuzzer_wordlist

    if(args.import_session):
        try:
            import_session(url_tree=url_tree, import_file=args.import_session)
        except (OSError, ValueError) as error:
            print(f"Could not import session {args.import_session}: {error}")
            exit(1)

    if(not url_tree.get("url")):
        print("A target is required: use -u <domain> or -is <session>")
        exit(1)

    # The target domain is always in scope, -d adds extra domains
    domains = [urlparse(url_tree["url"]).hostname]
    domains.extend(parse_domain(domain=domain) for domain in args.domain or [])

    if(args.auto_recon):
        auto_recon(depth=args.crawl_depth)
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
    7: lambda: deep_crawl(depth=read_positive_int(prompt="Depth: "), cookies=cookies, url_tree=url_tree, domains=domains, headers=headers),
    8: lambda: filter_scripts(node=url_tree, domains=domains, cookies=cookies, headers=headers),
    9: lambda: export_session(url_tree=url_tree),
}

    option = option.strip()

    if(not option.isdigit() or int(option) not in handle):
        print(f"Invalid option: {option}")
        return

    # Invalid URL numbers or depths only cancel the option, the session stays alive
    try:
        handle[int(option)]()
    except ValueError as error:
        print(f"Invalid input: {error}")

def auto_recon(depth):
    # Export even if something fails midway, so the crawled tree isn't lost
    try:
        deep_crawl(depth=depth, cookies=cookies, url_tree=url_tree, domains=domains, headers=headers)
        filter_scripts(node=url_tree, domains=domains, cookies=cookies, headers=headers)
        print("\n\nJavascript files saved in output/")
    finally:
        export_session(url_tree=url_tree)

def main():
    os.makedirs("output", exist_ok=True)

    option = load_args()

    while option != "0":
        print_menu()

        option = input("Choice: ")

        print()

        handle_option(option=option)


if __name__ == "__main__":
    main()