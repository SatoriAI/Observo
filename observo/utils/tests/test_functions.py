from unittest import TestCase

from ddt import data, ddt, unpack

from utils.config import RegexPatterns
from utils.functions import extract_calendly_uuid, extract_path_from_uri


@ddt
class TestFunctions(TestCase):
    @unpack
    @data(
        (
            "https://api.calendly.com/scheduled_events/7a248b8e-1a5d-4bc1-a177-361c8732b202",
            "/scheduled_events/7a248b8e-1a5d-4bc1-a177-361c8732b202",
        ),
        ("string", "string"),
    )
    def test_extract_path_from_uri(self, uri: str, expected: str) -> None:
        self.assertEqual(extract_path_from_uri(uri=uri), expected)

    @unpack
    @data(
        (
            "/scheduled_events/7a248b8e-1a5d-4bc1-a177-361c8732b202",
            "event",
            "7a248b8e-1a5d-4bc1-a177-361c8732b202",
        ),
        (
            "/scheduled_events/7a248b8e-1a5d-4bc1-a177-361c8732b202/invitees/8b2394b6-5cea-450e-80ce-e75280261381",
            "invitee",
            "8b2394b6-5cea-450e-80ce-e75280261381",
        ),
        *[("/scheduled_events/", key, None) for key in ["event", "invitee"]],
    )
    def test_extract_calendly_uuid(self, uri: str, group: str, expected: str | None) -> None:
        extracted = extract_calendly_uuid(pattern=RegexPatterns.CALENDLY_URI_PATTERN.value, string=uri, group=group)
        self.assertEqual(extracted, expected)
