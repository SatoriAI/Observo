import re
from datetime import datetime
from urllib.parse import urlparse


def extract_path_from_uri(uri: str) -> str:
    return urlparse(uri).path if "://" in uri else uri


def extract_calendly_uuid(pattern: re.Pattern, string: str, group: str | int) -> str | None:
    m = pattern.match(string)
    if not m:
        return None
    return m.group(group)


def get_time_based_greeting(locale: str | None = None, timezone_offset: int | None = None) -> str:
    """
    Returns a time-based greeting based on the user's locale and timezone.

    Args:
        locale: User's locale string (e.g., 'en-US', 'fr-FR', 'es-ES')
        timezone_offset: UTC offset in hours (-12 to +12), if known

    Returns:
        Appropriate greeting string
    """
    # Get current UTC time
    now = datetime.utcnow()

    # Apply timezone offset if provided
    if timezone_offset is not None:
        # Convert UTC hour to local hour
        local_hour = (now.hour + timezone_offset) % 24
    else:
        # Default to UTC if no timezone info
        local_hour = now.hour

    # Determine greeting based on hour
    if 5 <= local_hour < 12:
        greeting_base = "Good morning"
    elif 12 <= local_hour < 17:
        greeting_base = "Good afternoon"
    else:
        greeting_base = "Good evening"

    # Add language-specific variations based on locale
    if locale:
        locale_lower = locale.lower()

        # English (including US)
        if locale_lower.startswith("en"):
            # US English uses the same greetings as default English
            return f"{greeting_base},"

        # French
        elif locale_lower.startswith("fr"):
            if 5 <= local_hour < 12:
                return "Bonjour"
            elif 12 <= local_hour < 17:
                return "Bonjour"  # French uses "Bonjour" for afternoon too
            else:
                return "Bonsoir"

        # Spanish
        elif locale_lower.startswith("es"):
            if 5 <= local_hour < 12:
                return "Buenos días"
            elif 12 <= local_hour < 17:
                return "Buenas tardes"
            else:
                return "Buenas noches"

        # German
        elif locale_lower.startswith("de"):
            if 5 <= local_hour < 12:
                return "Guten Morgen"
            elif 12 <= local_hour < 17:
                return "Guten Tag"
            else:
                return "Guten Abend"

        # Italian
        elif locale_lower.startswith("it"):
            if 5 <= local_hour < 12:
                return "Buongiorno"
            elif 12 <= local_hour < 17:
                return "Buongiorno"  # Italian uses "Buongiorno" for afternoon too
            else:
                return "Buonasera"

        # Portuguese
        elif locale_lower.startswith("pt"):
            if 5 <= local_hour < 12:
                return "Bom dia"
            elif 12 <= local_hour < 17:
                return "Boa tarde"
            else:
                return "Boa noite"

        # Dutch
        elif locale_lower.startswith("nl"):
            if 5 <= local_hour < 12:
                return "Goedemorgen"
            elif 12 <= local_hour < 17:
                return "Goedemiddag"
            else:
                return "Goedenavond"

        # Swedish
        elif locale_lower.startswith("sv"):
            if 5 <= local_hour < 12:
                return "God morgon"
            elif 12 <= local_hour < 17:
                return "God eftermiddag"
            else:
                return "God kväll"

        # Norwegian
        elif locale_lower.startswith("no") or locale_lower.startswith("nb"):
            if 5 <= local_hour < 12:
                return "God morgen"
            elif 12 <= local_hour < 17:
                return "God ettermiddag"
            else:
                return "God kveld"

        # Danish
        elif locale_lower.startswith("da"):
            if 5 <= local_hour < 12:
                return "God morgen"
            elif 12 <= local_hour < 17:
                return "God eftermiddag"
            else:
                return "God aften"

        # Polish
        elif locale_lower.startswith("pl"):
            if 5 <= local_hour < 12:
                return "Dzień dobry"
            elif 12 <= local_hour < 17:
                return "Dzień dobry"  # Polish uses same greeting
            else:
                return "Dobry wieczór"

        # Russian
        elif locale_lower.startswith("ru"):
            if 5 <= local_hour < 12:
                return "Доброе утро"
            elif 12 <= local_hour < 17:
                return "Добрый день"
            else:
                return "Добрый вечер"

    # Default to English if locale not recognized or not provided
    return f"{greeting_base},"
