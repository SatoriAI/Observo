from unittest import TestCase
from unittest.mock import MagicMock, patch

import faker
import requests
from rest_framework import status

from utils.clients import CalendlyClient, CalendlyClientError

fake = faker.Faker()
MODULE = "utils.clients"


class CalendlyClientTests(TestCase):
    def setUp(self):
        self.base_url = "https://api.calendly.com"

        calendly_uuid = fake.uuid4()
        invitees_uuid = fake.uuid4()

        self.uri = f"/scheduled_events/{calendly_uuid}"
        self.invitee_uri = f"/scheduled_events/{calendly_uuid}/invitees/{invitees_uuid}"

        self.token = "TEST_TOKEN"

    @staticmethod
    def _mock_response(ok: bool = True, json_data: dict | None = None, code: int = status.HTTP_200_OK) -> MagicMock:
        resp = MagicMock()
        resp.ok = ok
        resp.status_code = code
        resp.json.return_value = json_data or {}
        return resp

    def test_headers_are_set_on_session(self):
        client = CalendlyClient(uri=self.uri, invitee_uri=self.invitee_uri, token=self.token)
        assert client.session.headers.get("Authorization") == f"Bearer {self.token}"
        assert "application/json" in client.session.headers.get("Accept")

    def test_get_event_success(self):
        client = CalendlyClient(uri=self.uri, invitee_uri=self.invitee_uri, token=self.token, timeout=5)

        event_payload = {
            "resource": {
                "start_time": "2025-08-20T09:00:00Z",
                "end_time": "2025-08-20T09:30:00Z",
                "name": "Intro Call",
            }
        }

        with patch(
            f"{MODULE}.requests.Session.get", return_value=self._mock_response(ok=True, json_data=event_payload)
        ) as get:
            data = client.get_event()

        self.assertEqual(
            data,
            {
                "start_time": "2025-08-20T09:00:00Z",
                "end_time": "2025-08-20T09:30:00Z",
                "name": "Intro Call",
            },
        )
        get.assert_called_once_with(self.uri, params=None, timeout=5)

    def test_get_invitee_success(self):
        client = CalendlyClient(uri=self.uri, invitee_uri=self.invitee_uri, token=self.token)

        email = fake.email()
        timezone = fake.timezone()
        invitee_payload = {"resource": {"email": email, "timezone": timezone}}

        with patch(
            f"{MODULE}.requests.Session.get", return_value=self._mock_response(ok=True, json_data=invitee_payload)
        ) as get:
            data = client.get_invitee()

        self.assertEqual(
            data,
            {
                "email": email,
                "name": None,
                "firstname": None,
                "lastname": None,
                "timezone": timezone,
            },
        )
        get.assert_called_once_with(self.invitee_uri, params=None, timeout=10)

    def test_missing_token_raises_exception(self):
        client = CalendlyClient(uri=self.uri, invitee_uri=self.invitee_uri, token="")  # force missing token

        with self.assertRaises(CalendlyClientError) as context:
            client.get_event()

        assert "Missing Calendly token (set CALENDLY_KEY)!" in str(context.exception)

    def test_http_error_raises_exception(self):
        client = CalendlyClient(self.uri, self.invitee_uri, token=self.token)

        with patch(
            f"{MODULE}.requests.Session.get",
            return_value=self._mock_response(ok=False, code=status.HTTP_401_UNAUTHORIZED),
        ) as get:
            with self.assertRaises(CalendlyClientError) as context:
                client.get_event()

        assert f"Calendly error {status.HTTP_401_UNAUTHORIZED}" in str(context.exception)
        get.assert_called_once_with(self.uri, params=None, timeout=10)

    def test_network_error_raises_exception(self):
        client = CalendlyClient(uri=self.uri, invitee_uri=self.invitee_uri, token=self.token)

        with patch(f"{MODULE}.requests.Session.get", side_effect=requests.RequestException("Malfunction")):
            with self.assertRaises(CalendlyClientError) as context:
                client.get_invitee()

        assert "Network error calling Calendly: Malfunction" in str(context.exception)

    def test_params_are_forwarded(self):
        client = CalendlyClient(uri=self.uri, invitee_uri=self.invitee_uri, token=self.token)

        with patch(f"{MODULE}.requests.Session.get", return_value=self._mock_response(ok=True)) as get:
            _ = client._get(self.uri, params={"count": 100})  # Call the private method just to assert params wiring

        get.assert_called_once_with(self.uri, params={"count": 100}, timeout=10)
