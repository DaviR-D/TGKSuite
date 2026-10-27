from html.parser import HTMLParser
import html
import re

URL_ATTRIBUTES = {"href", "src", "action", "formaction", "data", "poster", "background", "cite", "data-src", "data-href", "data-url"}
SRCSET_ATTRIBUTES = {"srcset", "imagesrcset"}
FORM_FIELD_TAGS = {"input", "select", "textarea", "button"}

# URLs inside scripts, JSON and inline code
ABSOLUTE_URL_REGEX = re.compile(r'https?://[^\s"\'`<>\\)]+')
QUOTED_PATH_REGEX = re.compile(r'["\'`](/[A-Za-z0-9_\-.~%][^"\'`\s<>\\]*)["\'`]')
META_REFRESH_REGEX = re.compile(r'url\s*=\s*[\'"]?([^\'"]+)', re.IGNORECASE)

TEXT_CONTENT_TYPES = ("text/", "javascript", "json", "xml")

class LinkParser(HTMLParser):
    """Collects the links, form params and <base href> of an HTML document."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = list()
        self.base_url = None
        self.current_form = None

    def add_link(self, url, params=None):
        link = {"url": url.strip(), "params": params if params is not None else list()}
        self.links.append(link)
        return link

    def handle_starttag(self, tag, attrs):
        attributes = {name: value for name, value in attrs if value is not None}

        if tag == "base" and "href" in attributes and self.base_url is None:
            self.base_url = attributes["href"].strip()

        if tag == "meta" and attributes.get("http-equiv", "").lower() == "refresh":
            match = META_REFRESH_REGEX.search(attributes.get("content", ""))
            if match:
                self.add_link(url=match.group(1))

        # Form fields become params of the form action (an empty action submits to the page itself)
        if tag == "form":
            self.current_form = self.add_link(url=attributes.get("action", ""))
        elif tag in FORM_FIELD_TAGS and self.current_form is not None and "name" in attributes:
            self.current_form["params"].append(f'{attributes["name"]}={attributes.get("value", "")}')

        for name, value in attributes.items():
            if name in URL_ATTRIBUTES and not (tag == "form" and name == "action"):
                self.add_link(url=value)
            elif name in SRCSET_ATTRIBUTES:
                for candidate in value.split(","):
                    if candidate.strip():
                        self.add_link(url=candidate.split()[0])

    def handle_endtag(self, tag):
        if tag == "form":
            self.current_form = None

def is_html(content_type):
    # Responses without a Content-Type are treated as HTML
    return not content_type or "html" in content_type.lower()

def is_text(content_type):
    return is_html(content_type=content_type) or any(text_type in content_type.lower() for text_type in TEXT_CONTENT_TYPES)

def extract_links(text, content_type):
    """Returns the page's <base href> (or None) and its links, as {"url", "params"} dicts."""
    if not is_text(content_type=content_type):
        return None, []

    base_url = None
    links = list()

    if is_html(content_type=content_type):
        parser = LinkParser()
        try:
            parser.feed(text)
            parser.close()
        except (AssertionError, ValueError):
            pass
        base_url = parser.base_url
        links.extend(parser.links)

    # JSON and JS often escape slashes as \/, HTML encodes & as &amp;
    text = text.replace("\\/", "/")

    if is_html(content_type=content_type):
        text = html.unescape(text)

    links.extend({"url": match.group(0), "params": list()} for match in ABSOLUTE_URL_REGEX.finditer(text))
    links.extend({"url": match.group(1), "params": list()} for match in QUOTED_PATH_REGEX.finditer(text))

    return base_url, links
