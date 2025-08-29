from scapy.all import sniff, rdpcap, Raw
import logging
import argparse
from logging.handlers import RotatingFileHandler
from collections import defaultdict, deque
import time
import re
import sys

# -------------------- Configuration / thresholds --------------------
RATE_WINDOW_SECONDS = 10 # sliding window for rate detection
RATE_THRESHOLD = 20 # requests per window considered suspicious
DISTINCT_HOSTS_THRESHOLD = 10 # many distinct hosts requested by same src
MAX_HOST_LENGTH = 255
ANOMALY_LOG_MAX_BYTES = 5 * 1024 * 1024
ANOMALY_BACKUP_COUNT = 3


HTTP_METHODS = (b'GET', b'POST', b'HEAD', b'PUT', b'DELETE', b'OPTIONS', b'PATCH')


SUSPICIOUS_PATH_PATTERNS = [
re.compile(rb"\b(select|union|insert|drop|update)\b", re.I),
re.compile(rb"\.{2,}"), # directory traversal This regex looks for two or more dots in a row, e.g. ../ or ....//.
re.compile(rb"/etc/passwd"),
]


HOST_VALID_RE = re.compile(r"^[A-Za-z0-9.-:]+$")#he regex makes sure the Host: header:is not empty,only contains expected characters for a hostname (and optional port),
#doesn’t contain whitespace, quotes, slashes, or injection characters.

def setup_logging(logFile=None, level=logging.INFO):
    logger = logging.getLogger("http_sniffer")
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    sh= logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    if logFile:
        fh = RotatingFileHandler(logFile, maxBytes=ANOMALY_LOG_MAX_BYTES, backupCount=ANOMALY_BACKUP_COUNT)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger

class AnomalyDetector:
    def __init__(self, rate_window=RATE_WINDOW_SECONDS,
                 rate_threshold=RATE_THRESHOLD,
                 distinct_hosts_threshold=DISTINCT_HOSTS_THRESHOLD):
        self.request_times = defaultdict(lambda: deque())
        self.hosts_seen = defaultdict(set)
        self.total_requests = defaultdict(int)
        self.rate_window = rate_window
        self.rate_threshold = rate_threshold
        self.distinct_hosts_threshold = distinct_hosts_threshold
    
    def add_request(self, src_ip, host, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
            dq = self.request_times[src_ip]
            dq.append(timestamp)
            self.total_requests[src_ip] += 1
            if host:
                self.hosts_seen[src_ip].add(host)
                self._prune_old(src_ip, now=timestamp)

    def _prune_old(self, src_ip, now=None):
        now = now or time.time()
        dq = self.request_times[src_ip]
        while dq and (now - dq[0] > self.rate_window):
            dq.popleft()


    def check_rate_anomaly(self, src_ip):
        return len(self.request_times[src_ip]) > self.rate_threshold


    def check_many_hosts(self, src_ip):
        return len(self.hosts_seen[src_ip]) > self.distinct_hosts_threshold


    def summary_for(self, src_ip):
        return {
            'total_requests': self.total_requests[src_ip],
            'recent_rate': len(self.request_times[src_ip]),
            'distinct_hosts': len(self.hosts_seen[src_ip]),
        }
    
# -------------------- HTTP Host parsing --------------------


def parse_http_host(raw_bytes):
    """Return (host, path, method) or (None, None, None) if no HTTP request found."""
    try:
       # ensure bytes
        if not isinstance(raw_bytes, (bytes, bytearray)):
         return (None, None, None)


      # quick heuristic: starts with HTTP method
        start = raw_bytes.lstrip()
        if not any(start.startswith(m) for m in HTTP_METHODS):
         # sometimes payload may include preceding headers, attempt to find a request-line
            first_line_end = raw_bytes.find(b"\r\n")
            if first_line_end == -1:
                return (None, None, None)
            first_line = raw_bytes[:first_line_end]
            if not any(first_line.startswith(m) for m in HTTP_METHODS):
                return (None, None, None)
            # split lines
        lines = raw_bytes.split(b"\r\n")
        # request-line is first non-empty line
        req_line = None
        for ln in lines:
            if ln.strip():
              req_line = ln
              break
        if req_line is None:
            return (None, None, None)

        parts = req_line.split()
        method = parts[0].decode(errors='ignore') if parts else None
        path = parts[1].decode(errors='ignore') if len(parts) > 1 else None


        host = None
        for ln in lines:
            if ln.lower().startswith(b'host:'):
            # Host: header may contain spaces
                host = ln.split(b':', 1)[1].strip().decode(errors='ignore')
                break
        return (host, path, method)
    except Exception:
      return (None, None, None)
    
if __name__ == "__main__":
    logger = setup_logging()
    detector = AnomalyDetector()

    src_ip = "192.168.1.100"

    # simulate 25 requests in quick succession
    for i in range(25):
        detector.add_request(src_ip, host=f"example{i%3}.com")
        time.sleep(0.05)  # small delay so timestamps are slightly different

    # print summary
    summary = detector.summary_for(src_ip)
    logger.info(f"Summary for {src_ip}: {summary}")

    # check anomalies
    if detector.check_rate_anomaly(src_ip):
        logger.warning(f"Rate anomaly detected for {src_ip}")

    if detector.check_many_hosts(src_ip):
        logger.warning(f"Host anomaly detected for {src_ip}")

