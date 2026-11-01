from contextlib import redirect_stdout
from urllib.parse import urlparse
import argparse
import math
import os
import re
from crawler import crawl_one, crawl_all, deep_crawl
from fuzzer import fuzz
from jsonl_tree import JsonlTreeWriter, JSONL_PATH
from rate_limit import RateLimiter
from request_log import LOGS_DIR, create_logs_dir
from scan import Scan
from scripts import save_scripts
from session import export_session, import_session
from url_tree import find_node_by_number, new_node
from utils import OUTPUT_DIR
from visual import print_menu, print_url_tree, print_params

DEFAULT_CRAWL_DEPTH = 3

DESCRIPTION = """TeigekiSuite - web recon toolkit: crawling, script collection and fuzzing.

Without -a, an interactive menu opens to crawl, fuzz and inspect the URL tree.
Requests only go over https to the target domain, its subdomains and -d domains;
redirects leaving that scope are blocked, so cookies and headers never leak."""

EXAMPLES = [
    ("-t example.com", "open the interactive menu"),
    ("-t example.com -a", f"crawl {DEFAULT_CRAWL_DEPTH} levels, save scripts, export session"),
    ("-t example.com -a -cd 5", "automatic recon 5 levels deep"),
    ("-t example.com -d api.example.net", "also allow requests to api.example.net"),
    ("-t example.com -x blog.example.com", "crawl example.com but never its blog subdomain"),
    ("-t example.com -c session=abc -H \"Authorization: Bearer xyz\"", "authenticated crawling"),
    (f"-is {OUTPUT_DIR}/url_tree.json", "resume a previous session"),
    ("-t example.com -a -l", f"automatic recon saving every request and response in {LOGS_DIR}/"),
    ("-t example.com -a -r 2", "automatic recon sending at most 2 requests per second"),
    ("-t example.com -a -ia", f"silent automatic recon, streaming the URL tree to {JSONL_PATH} live"),
]

def build_epilog():
    examples = "\n\n".join(f"  # {explanation}\n  %(prog)s {command}" for command, explanation in EXAMPLES)

    return f"examples:\n{examples}\n\noutput files (scripts, fuzzing results, session) are saved in {OUTPUT_DIR}/"

def build_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=build_epilog(), formatter_class=argparse.RawDescriptionHelpFormatter)

    target = parser.add_argument_group("target (one is required)")
    target.add_argument("-t", "--target", metavar="DOMAIN", help="target domain, optionally with port (e.g. example.com, example.com:8443); crawled over https")
    target.add_argument("-is", "--import-session", metavar="FILE", help="resume from a session file exported earlier (takes precedence over -t)")

    scope = parser.add_argument_group("scope")
    scope.add_argument("-d", "--domain", metavar="DOMAIN", action="append", help="extra in-scope domain, subdomains included (repeatable)")
    scope.add_argument("-x", "--exclude", metavar="DOMAIN", action="append", help="out-of-scope domain, subdomains included, blocked even under an in-scope domain (repeatable)")

    authentication = parser.add_argument_group("authentication")
    authentication.add_argument("-c", "--cookie", metavar="KEY=VALUE", action="append", help="cookie sent with every request (repeatable)")
    authentication.add_argument("-H", "--header", metavar="\"NAME: VALUE\"", action="append", help="header sent with every request (repeatable)")

    recon = parser.add_argument_group("automatic recon")
    recon.add_argument("-a", "--auto-recon", action="store_true", help="crawl, save the javascript files found and export the session, without the menu")
    recon.add_argument("-cd", "--crawl-depth", metavar="N", type=int, default=DEFAULT_CRAWL_DEPTH, help=f"how many levels -a crawls (default: {DEFAULT_CRAWL_DEPTH})")
    recon.add_argument("-ia", "--auto-recon-jsonl", action="store_true", help=f"with -a, print nothing and stream the URL tree to {JSONL_PATH} as it's crawled (one JSON node per line)")

    fuzzing = parser.add_argument_group("fuzzing")
    fuzzing.add_argument("-fw", "--fuzzer-wordlist", metavar="FILE", help="wordlist used by the menu's fuzz option (asked for when omitted)")

    requests_group = parser.add_argument_group("requests")
    requests_group.add_argument("-r", "--rate-limit", metavar="N", type=float, help="send at most N requests per second, in every feature (e.g. 5, or 0.5 for one every 2s); unlimited by default")
    requests_group.add_argument("-l", "--log-requests", action="store_true", help=f"save every request and its full response in {LOGS_DIR}/, one file each (includes cookies and auth headers)")

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

    raise ValueError("a target is required: use -t DOMAIN or -is FILE")

def build_scan(args):
    url_tree = load_url_tree(args=args)

    # The target domain is always in scope, -d adds extra domains
    domains = [urlparse(url_tree["url"]).hostname]
    domains.extend(parse_domain(domain=domain) for domain in args.domain or [])

    # -x blocks domains even when they fall under an in-scope domain (e.g. an out-of-scope subdomain)
    excluded_domains = [parse_domain(domain=domain) for domain in args.exclude or []]

    cookies = dict(parse_key_value(item=cookie, separator="=", expected_format="key=value") for cookie in args.cookie or [])
    headers = dict(parse_key_value(item=header, separator=":", expected_format="Name: Value") for header in args.header or [])

    return Scan(url_tree=url_tree, domains=domains, excluded_domains=excluded_domains, cookies=cookies, headers=headers,
                log_requests=args.log_requests, rate_limiter=RateLimiter(requests_per_second=args.rate_limit))

def run_auto_recon(scan, depth):
    # Export even if something fails midway, so the crawled tree isn't lost
    try:
        deep_crawl(depth=depth, scan=scan)
        save_scripts(node=scan.url_tree, scan=scan)
        print(f"\n\nJavascript files saved in {OUTPUT_DIR}/")
    finally:
        export_session(url_tree=scan.url_tree)

def run_auto_recon_jsonl(scan, depth):
    """Runs -a with no terminal output, streaming every node to the jsonl file as it's found."""
    writer = JsonlTreeWriter()
    scan.node_sink = writer.record

    try:
        # The root isn't found as anyone's child, so record it before crawling starts
        writer.record(scan.url_tree)

        # Everything -a prints is swallowed; the live jsonl file is the only output
        with open(os.devnull, "w", encoding="utf-8") as devnull, redirect_stdout(devnull):
            run_auto_recon(scan=scan, depth=depth)
    finally:
        writer.close()

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

    if args.rate_limit is not None and not (math.isfinite(args.rate_limit) and args.rate_limit > 0):
        parser.error(f"argument -r/--rate-limit: expected a positive number, got {args.rate_limit}")

    if args.crawl_depth < 1:
        parser.error(f"argument -cd/--crawl-depth: expected a positive integer, got {args.crawl_depth}")

    if args.auto_recon_jsonl and not args.auto_recon:
        parser.error("argument -ia/--auto-recon-jsonl: only works together with -a/--auto-recon")

    try:
        scan = build_scan(args=args)
    except ValueError as error:
        parser.error(str(error))

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if scan.log_requests:
        create_logs_dir()

    if args.auto_recon and args.auto_recon_jsonl:
        run_auto_recon_jsonl(scan=scan, depth=args.crawl_depth)
    elif args.auto_recon:
        run_auto_recon(scan=scan, depth=args.crawl_depth)
    else:
        run_menu(scan=scan, fuzzing_wordlist=args.fuzzer_wordlist)


if __name__ == "__main__":
    main()
