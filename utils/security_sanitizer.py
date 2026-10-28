"""
GPT-OPS Security Sanitizer & Target Validation
Validates target format and prevents command injection.
"""

import os
import re
import ipaddress
from typing import Tuple

# Cloud metadata endpoints to prevent accidental metadata query loops
METADATA_IPS = [
    ipaddress.ip_network("169.254.169.254/32"),
]

DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)
HOSTNAME_REGEX = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9_-]{0,62})$"
)

def sanitize_and_validate_target(target: str) -> Tuple[bool, str, str]:
    """
    Sanitizes and validates a target domain, hostname, or IP.
    Returns: (is_valid: bool, clean_target: str, error_message: str)
    """
    if not target or not isinstance(target, str):
        return False, "", "Target input cannot be empty."

    # Strip protocols, whitespace, and port/path suffixes
    clean = target.strip().lower()
    clean = re.sub(r"^https?://", "", clean)
    clean = re.sub(r"^ftp://", "", clean)
    clean = re.sub(r"^ssh://", "", clean)
    clean = clean.split("/")[0].split(":")[0]

    # Prevent shell injection characters in target string
    if any(c in clean for c in [';', '&', '|', '`', '$', ' ', '<', '>', '"', "'", '\\', '\n', '\r']):
        return False, "", "Target contains illegal characters."

    if not clean:
        return False, "", "Target format is invalid."

    # Check for cloud metadata service protection
    try:
        ip_obj = ipaddress.ip_address(clean)
        for meta_net in METADATA_IPS:
            if ip_obj in meta_net:
                return False, "", "Targeting cloud metadata endpoint is prohibited."
        return True, str(ip_obj), ""
    except ValueError:
        pass

    if clean in ["metadata.google.internal", "instance-data"]:
        return False, "", "Targeting cloud metadata domain is prohibited."

    # Allow valid domain names or internal network hostnames (e.g. dc01, lab-server)
    if DOMAIN_REGEX.match(clean) or HOSTNAME_REGEX.match(clean):
        return True, clean, ""

    return False, "", "Target must be a valid hostname, domain, or IP address."
