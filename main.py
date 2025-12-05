import argparse
import fuzzer
import crawler

target_urls_tree = dict()

def main():
    methods = [print, fuzzing, crawling]

    option = 99
    parser = argparse.ArgumentParser(description="ShingekiSuite")
    parser.add_argument("-u", "--url", help="Target URL")
    args = parser.parse_args()
    target_urls_tree["root_url"] = args.url

    while option != "0":
        print_menu()

        option = input("Choice: ")

        methods[int(option)]()
            

def print_menu():
    print(f"Root URL: {target_urls_tree["root_url"]}")

    print("1) Fuzz")
    print("2) Crawl")
    print("0) Exit")

def fuzzing():
    print("Available URLs: ")
    print(f"1. {target_urls_tree["root_url"]}")
    target_url = input("Target URL: ")
    wordlist_path = input("Wordlist: ")
    target_url = target_urls_tree["root_url"]
    fuzzer.fuzz(target_url, wordlist_path)

def crawling():
    crawler.crawl(target_urls_tree["root_url"])

if __name__ == "__main__":
    main()