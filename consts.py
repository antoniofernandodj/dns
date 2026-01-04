from enum import Enum

GOOGLE_DNS = "8.8.8.8"
CLOUDFLARE_DNS = "1.0.0.1"
TTL = 60
MEDIUM_TTL = 300
LONG_TTL = 3600


class DNSResolutionStatus(Enum):
    SUCCESS = "success"
    NXDOMAIN = "nxdomain"
    NO_ANSWER = "no_answer"
    TIMEOUT = "timeout"
    NO_NAMESERVERS = "no_nameservers"
    INVALID_INPUT = "invalid_input"
    DNS_ERROR = "dns_error"
    UNKNOWN_ERROR = "unknown_error"
