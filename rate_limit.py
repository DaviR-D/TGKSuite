import time

class RateLimiter:
    """Spaces requests out so no more than requests_per_second are sent. None means unlimited."""

    def __init__(self, requests_per_second=None):
        self.interval = 1 / requests_per_second if requests_per_second else 0
        self.next_request_time = 0.0

    def wait(self):
        if not self.interval:
            return

        now = time.monotonic()

        if now < self.next_request_time:
            time.sleep(self.next_request_time - now)

        self.next_request_time = max(now, self.next_request_time) + self.interval
