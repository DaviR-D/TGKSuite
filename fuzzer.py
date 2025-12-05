from time import sleep
import requests

def loadWordlist(file_path):
    with open(file_path, 'r', encoding='utf-8') as wordlist:
        return wordlist.read().split('\n')

def fuzz(target, wordlist_path, delay_time=0):
    with open("output/fuzz.txt", 'w+', encoding='utf-8') as output:
        wordlist = loadWordlist(wordlist_path)
        for payload in wordlist:
            response = exception_safe_request(target, payload)
            result = f"{response.status_code} | {payload} | {response.elapsed.total_seconds()}"
            output.write(result + "\n")
            print(result)
            sleep(delay_time)

def exception_safe_request(target, payload):
    while True:
        try:
            return requests.get(f'{target}/{payload}', timeout=5)
        except:
            sleep(1)