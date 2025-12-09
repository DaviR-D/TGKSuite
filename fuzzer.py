from time import sleep
import requests

def loadWordlist(file_path):
    with open(file_path, 'r', encoding='utf-8') as wordlist:
        return wordlist.read().split('\n')

def fuzz(target, wordlist_path, cookies, delay_time=0):
    output_file_name = '-'.join(target.split('/'))

    with open(f"output/{output_file_name}.txt", 'w+', encoding='utf-8') as output:
        wordlist = loadWordlist(wordlist_path)
        for payload in wordlist:
            response = exception_safe_request(target, payload, cookies)
            result = f"{response.status_code} | {payload} | {response.elapsed.total_seconds()}"
            output.write(result + "\n")
            print(result)
            sleep(delay_time)

def exception_safe_request(target, payload, cookies):
    while True:
        try:
            return requests.get(f'{target}/{payload}/', cookies=cookies, timeout=5)
        except:
            sleep(1)

def fuzzing(target_url, fuzzing_wordlist, cookies):
    if(not fuzzing_wordlist or len(fuzzing_wordlist) == 0):
        fuzzing_wordlist = input("Wordlist: ")

    print()
        
    fuzz(target_url["url"], fuzzing_wordlist, cookies)

    print()