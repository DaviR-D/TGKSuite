from urllib.parse import urlparse
import argparse
import os
import re
from crawler import crawl_one, crawl_all, deep_crawl
from fuzzer import fuzz
from scan import Scan
from scripts import save_scripts
from session import export_session, import_session
from url_tree import find_node_by_number, new_node
from utils import OUTPUT_DIR
from visual import print_menu, print_url_tree, print_params

DEFAULT_CRAWL_DEPTH = 3

def build_parser():
    parser = argparse.ArgumentParser(description="TeigekiSuite")
    parser.add_argument("-t", "--target", help="Target domain, e.g. example.com (crawled over https and used as the default scope)", metavar="domain")
    parser.add_argument("-is", "--import-session", help="Import previous session", metavar="session")
    parser.add_argument("-fw", "--fuzzer-wordlist", help="Set fixed fuzzing wordlist", metavar="wordlist")
    parser.add_argument("-d", "--domain", help="Additional in-scope domain (multiple uses supported)", action="append", metavar="domain")
    parser.add_argument("-c", "--cookie", help="Cookie (key=value, multiple uses supported)", action="append", metavar="cookie")
    parser.add_argument("-H", "--header", help="Custom HTTP header (\"Name: Value\", multiple uses supported)", action="append", metavar="header")
    parser.add_argument("-a", "--auto-recon", help="Perform default automatic recon", action="store_true")
    parser.add_argument("-cd", "--crawl-depth", help=f"Crawling depth used by the automatic recon (default: {DEFAULT_CRAWL_DEPTH})", type=int, default=DEFAULT_CRAWL_DEPTH, metavar="depth")

    return parser

def parse_positive_int(value):
    value = value.strip()

    if not value.isdigit() or int(value) < 1:
        raise ValueError(f"expected a positive integer, got {value}")

    return int(value)

def parse_domain(domain, allow_port=False):
    domain = domain.strip().lower().rstrip(".")
    port_regex = r"(:[0-9]{1,5})?" if allow_port else ""

    if not re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)*" + port_regex, domain):
        raise ValueError(f"invalid domain {domain} (expected e.g. example.com, without scheme or path{'' if allow_port else ' or port'})")

    # 443 is the https default, keeping it would duplicate URLs found without it
    return domain.removesuffix(":443")

def parse_key_value(item, separator, expected_format):
    if separator not in item:
        raise ValueError(f"invalid value {item} (expected \"{expected_format}\")")

    key, value = item.split(separator, 1)

    return key.strip(), value.strip()

def load_url_tree(args):
    if args.import_session:
        try:
            return import_session(import_file=args.import_session)
        except (OSError, ValueError) as error:
            raise ValueError(f"could not import session {args.import_session}: {error}")

    if args.target:
        return new_node(url=f"https://{parse_domain(domain=args.target, allow_port=True)}")

    raise ValueError("a target is required: use -t <domain> or -is <session>")

def build_scan(args):
    url_tree = load_url_tree(args=args)

    # The target domain is always in scope, -d adds extra domains
    domains = [urlparse(url_tree["url"]).hostname]
    domains.extend(parse_domain(domain=domain) for domain in args.domain or [])

    cookies = dict(parse_key_value(item=cookie, separator="=", expected_format="key=value") for cookie in args.cookie or [])
    headers = dict(parse_key_value(item=header, separator=":", expected_format="Name: Value") for header in args.header or [])

    return Scan(url_tree=url_tree, domains=domains, cookies=cookies, headers=headers)

def run_auto_recon(scan, depth):
    # Export even if something fails midway, so the crawled tree isn't lost
    try:
        deep_crawl(depth=depth, scan=scan)
        save_scripts(node=scan.url_tree, scan=scan)
        print(f"\n\nJavascript files saved in {OUTPUT_DIR}/")
    finally:
        export_session(url_tree=scan.url_tree)

def ask_node(scan):
    return find_node_by_number(number=input("Target URL: "), node=scan.url_tree)

def build_menu_options(scan, fuzzing_wordlist):
    return {
        1: ("Fuzz", lambda: fuzz(node=ask_node(scan=scan), wordlist_path=fuzzing_wordlist or input("Wordlist: "), scan=scan)),
        2: ("Crawl", lambda: crawl_one(node=ask_node(scan=scan), scan=scan)),
        3: ("Show available URLs", lambda: print_url_tree(node=scan.url_tree)),
        4: ("Print params", lambda: print_params(node=ask_node(scan=scan))),
        5: ("Print URLs and params", lambda: print_url_tree(node=scan.url_tree, include_params=True)),
        6: ("Crawl all URLs once", lambda: crawl_all(node=scan.url_tree, scan=scan)),
        7: ("Crawl all URLs in-depth", lambda: deep_crawl(depth=parse_positive_int(value=input("Depth: ")), scan=scan)),
        8: ("Save scripts", lambda: save_scripts(node=scan.url_tree, scan=scan)),
        9: ("Export URL tree", lambda: export_session(url_tree=scan.url_tree)),
        0: ("Exit", None),
    }

def run_menu(scan, fuzzing_wordlist):
    menu_options = build_menu_options(scan=scan, fuzzing_wordlist=fuzzing_wordlist)

    while True:
        print_menu(menu_options=menu_options)
        option = input("Choice: ").strip()
        print()

        if not option.isdigit() or int(option) not in menu_options:
            print(f"Invalid option: {option}")
            continue

        _, action = menu_options[int(option)]

        if action is None:
            return

        # Invalid URL numbers or depths only cancel the option, the session stays alive
        try:
            action()
        except ValueError as error:
            print(f"Invalid input: {error}")

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.crawl_depth < 1:
        parser.error(f"argument -cd/--crawl-depth: expected a positive integer, got {args.crawl_depth}")

    try:
        scan = build_scan(args=args)
    except ValueError as error:
        parser.error(str(error))

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.auto_recon:
        run_auto_recon(scan=scan, depth=args.crawl_depth)
    else:
        run_menu(scan=scan, fuzzing_wordlist=args.fuzzer_wordlist)


if __name__ == "__main__":
    main()
