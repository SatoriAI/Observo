import re
from datetime import datetime
from urllib.parse import urlparse

import pytz
from timezonefinder import TimezoneFinder


def extract_path_from_uri(uri: str) -> str:
    return urlparse(uri).path if "://" in uri else uri


def extract_calendly_uuid(pattern: re.Pattern, string: str, group: str | int) -> str | None:
    m = pattern.match(string)
    if not m:
        return None
    return m.group(group)


def compute_greetings(latitude: float, longitude: float) -> str:
    try:
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=latitude, lng=longitude)

        if not timezone_str:  # Fallback to UTC if timezone cannot be determined
            timezone_str = "UTC"

        user_timezone = pytz.timezone(timezone_str)

        current_time = datetime.now(user_timezone)
        hour = current_time.hour

        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 18:
            return "Good afternoon"
        else:
            return "Good evening"
    except Exception:
        return "Hello"
