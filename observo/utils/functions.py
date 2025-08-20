import re
from urllib.parse import urlparse


def extract_path_from_uri(uri: str) -> str:
    return urlparse(uri).path if "://" in uri else uri


def extract_calendly_uuid(pattern: re.Pattern, string: str, group: str | int) -> str | None:
    m = pattern.match(string)
    if not m:
        return None
    return m.group(group)
