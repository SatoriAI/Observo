import requests

from observo import settings


class CalendlyClientError(Exception):
    pass


class CalendlyClient:
    def __init__(self, uri: str, invitee_uri: str, *, token: str | None = None, timeout: int = 10) -> None:
        self.uri = uri
        self.invitee_uri = invitee_uri

        self.token = token if token is not None else settings.CALENDLY_KEY
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def get_event(self) -> dict:
        data = self._get(self.uri)
        return {
            "start_time": data.get("resource", {}).get("start_time"),
            "end_time": data.get("resource", {}).get("end_time"),
            "name": data.get("resource", {}).get("name"),
        }

    def get_invitee(self) -> dict:
        data = self._get(self.invitee_uri)
        return {
            "email": data.get("resource", {}).get("email"),
            "name": data.get("resource", {}).get("name"),
            "firstname": data.get("resource", {}).get("first_name"),
            "lastname": data.get("resource", {}).get("last_name"),
            "timezone": data.get("resource", {}).get("timezone"),
        }

    def _get(self, path: str, params: dict | None = None) -> dict:
        if not self.token:
            raise CalendlyClientError("Missing Calendly token (set CALENDLY_KEY)!")

        try:
            resp = self.session.get(path, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise CalendlyClientError(f"Network error calling Calendly: {exc}") from exc

        if not resp.ok:
            raise CalendlyClientError(f"Calendly error {resp.status_code} for {path}")

        return resp.json()
