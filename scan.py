from dataclasses import dataclass, field

@dataclass
class Scan:
    """Everything a request needs to know about the current target."""
    url_tree: dict
    domains: list
    cookies: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    log_requests: bool = False
