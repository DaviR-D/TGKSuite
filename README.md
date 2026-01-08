# **TeigekiSuite**

TeigekiSuite is a lightweight, modular web-security toolkit focused on crawling, fuzzing, and session-based exploration of web applications. It provides an interactive workflow for mapping URL structures, identifying potential attack surfaces, and performing fuzzing tests using custom wordlists.

---

## **Features**

### 🔍 Crawler

* Recursively parses web pages and extracts links.
* Builds a structured URL tree representing application navigation.
* Supports optional cookies for authenticated crawling.

### 🧪 Fuzzer

* Sends fuzzing payloads to discovered endpoints.
* Accepts customizable wordlists.
* Stores results in organized output files.
* Works seamlessly with the crawler's URL tree.

### 📁 Session Management

* Save and load sessions to continue work later.
* Store URL trees and fuzzing results.
* Easily import/export session files.

### 📊 Visual Tree Renderer

* Displays the URL tree structure in a clean, readable format.
* Helps visualize site hierarchy and potential attack paths.

## **Usage**

### Start crawling

```bash
python3 main.py -u https://target.com
```

### Load a previous session

```bash
python3 main.py -is session.json
```

### Use cookies

```bash
python3 main.py -c "SESSIONID=12345; token=abcd"
```

### Run fuzzing

```bash
python3 main.py -u https://target.com -fw wordlists/common.txt
```

## **How It Works**

1. **Crawler:** Fetches a URL, extracts links, recursively builds a tree.
2. **Fuzzer:** Injects payloads into endpoints and logs anomalies.
3. **Session Tools:** Store all states into JSON for later use.
4. **Visualization:** Renders the URL tree using a clean textual structure.

---

## **Planned Improvements**

* Concurrent crawling and fuzzing
* More robust HTML parsing
* Response diffing for anomaly detection

