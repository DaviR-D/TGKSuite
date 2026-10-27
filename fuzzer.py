from time import sleep
import requests
from http_client import safe_get, OutOfScopeError
from utils import safe_filename

MAX_RETRIES = 3

def loadWordlist(file_path):
    with open(file_path, 'r', encoding='utf-8') as wordlist:
        return [line for line in wordlist.read().split('\n') if line.strip()]

def fuzz(target, wordlist_path, cookies, domains, delay_time=0, headers=None):
    output_file_name = safe_filename(name=target, extension=".txt")

    try:
        wordlist = loadWordlist(file_path=wordlist_path)
    except (OSError, UnicodeDecodeError) as error:
        print(f"Could not read wordlist {wordlist_path}: {error}")
        return

    with open(f"output/{output_file_name}", 'w+', encoding='utf-8') as output:
        for payload in wordlist:
            response = exception_safe_request(target=target, payload=payload, cookies=cookies, domains=domains, headers=headers)
            if isinstance(response, str):
                result = f"{response} | {payload} | -"
            else:
                result = f"{response.status_code} | {payload} | {response.elapsed.total_seconds()}"
            output.write(result + "\n")
            print(result)
            sleep(delay_time)

def exception_safe_request(target, payload, cookies, domains, headers=None):
    for _ in range(MAX_RETRIES):
        try:
            return safe_get(url=f'{target}/{payload}/', domains=domains, cookies=cookies, headers=headers, timeout=5)
        except OutOfScopeError:
            return "OUT-OF-SCOPE"
        except requests.exceptions.RequestException:
            sleep(1)

    return "ERROR"

def fuzzing(target_url, fuzzing_wordlist, cookies, domains, headers=None):
    if(not fuzzing_wordlist or len(fuzzing_wordlist) == 0):
        fuzzing_wordlist = input("Wordlist: ")

    print()
        
    fuzz(target=target_url["url"], wordlist_path=fuzzing_wordlist, cookies=cookies, domains=domains, headers=headers)

    print()