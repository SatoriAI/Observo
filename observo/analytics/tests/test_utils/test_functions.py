from unittest import TestCase

from ddt import data, ddt, unpack

from analytics.utils.functions import hash_ip


@ddt
class TestFunctions(TestCase):
    @unpack
    @data(
        (None, None),
        ("192.168.1.1", "75ac09f12c80a597d71abbd8101814416793544ba29d2f58c87db63273080d1d"),
    )
    def test_hash_ip(self, ip_address: str | None, expected: str | None) -> None:
        self.assertEqual(hash_ip(ip_address=ip_address), expected)
