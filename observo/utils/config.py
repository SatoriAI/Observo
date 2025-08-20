import re
from enum import Enum


class RegexPatterns(Enum):
    CALENDLY_URI_PATTERN = re.compile(r"^/scheduled_events/(?P<event>[^/]+)(?:/invitees/(?P<invitee>[^/?#]+))?$")
