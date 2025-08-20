import datetime
from typing import Any
from unittest.mock import patch

import faker
from ddt import data, ddt, unpack
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from analytics.models import Contact, Meeting, Survey
from analytics.tests.factories import SurveyFactory

fake = faker.Faker()


class ContactCreateViewTestCase(APITestCase):
    URL = reverse("analytics:api-contacts-create")

    def test_create_contact_success(self) -> None:
        survey = SurveyFactory()
        payload = {"survey": survey.pk, "email": fake.email()}

        response = self.client.post(self.URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contact.objects.count(), 1)

        contact = Contact.objects.first()
        self.assertEqual(contact.survey, survey)
        self.assertEqual(contact.email, payload["email"])

    def test_create_contact_missing_email(self) -> None:
        survey = SurveyFactory()
        payload = {"survey": survey.pk}

        response = self.client.post(self.URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"email": ["This field is required."]})

        self.assertEqual(Contact.objects.count(), 0)


@ddt
class MeetingCreateViewTestCase(APITestCase):
    URL = reverse("analytics:api-meetings-create")

    def test_create_meeting_success(self) -> None:
        survey = SurveyFactory()

        uri = fake.uri()
        invitee_uri = fake.uri()

        start_time = fake.iso8601(datetime.UTC)
        end_time = fake.iso8601(datetime.UTC)
        name = fake.company()

        invitee = fake.email()
        nickname = fake.name()
        timezone = fake.timezone()

        payload = {"survey": survey.pk, "uri": uri, "invitee_uri": invitee_uri}

        with patch(
            "analytics.api.serializers.CalendlyClient.get_event",
            return_value={
                "start_time": start_time,
                "end_time": end_time,
                "name": name,
            },
        ) as get_calendly_event:
            with patch(
                "analytics.api.serializers.CalendlyClient.get_invitee",
                return_value={
                    "email": invitee,
                    "name": nickname,
                    "firstname": None,
                    "lastname": None,
                    "timezone": timezone,
                },
            ) as get_calendly_invitee:
                response = self.client.post(self.URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Meeting.objects.count(), 1)

        get_calendly_event.assert_called_once_with()
        get_calendly_invitee.assert_called_once_with()

        meeting = Meeting.objects.first()
        self.assertEqual(meeting.survey, survey)

        self.assertEqual(meeting.uri, uri)
        self.assertEqual(meeting.invitee_uri, invitee_uri)

        # Invitee information
        self.assertEqual(meeting.email, invitee)
        self.assertEqual(meeting.nickname, nickname)
        self.assertIsNone(meeting.firstname)
        self.assertIsNone(meeting.lastname)
        self.assertEqual(meeting.timezone, timezone)

        # Meeting information
        self.assertEqual(meeting.start.isoformat(), start_time)
        self.assertEqual(meeting.finish.isoformat(), end_time)
        self.assertEqual(meeting.name, name)

    @unpack
    @data(
        ({"uri": fake.uri()}, {"invitee_uri": ["This field is required."]}),
        ({"invitee_uri": fake.uri()}, {"uri": ["This field is required."]}),
    )
    def test_create_meeting_missing_fields(self, payload: dict, error: dict) -> None:
        survey = SurveyFactory()

        response = self.client.post(self.URL, {"survey": survey.pk} | payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), error)

        self.assertEqual(Contact.objects.count(), 0)


@ddt
class SurveyCreateViewTestCase(APITestCase):
    URL = reverse("analytics:api-surveys-create")

    def test_create_survey_success(self) -> None:
        payload = {"answers": {"1": "A", "2": "B", "3": "A", "4": "B"}, "sector": "Some Sector", "threshold": 3}

        response = self.client.post(self.URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Survey.objects.count(), 1)

        survey = Survey.objects.first()
        self.assertEqual(survey.answers, payload["answers"])
        self.assertEqual(survey.sector, payload["sector"])
        self.assertEqual(survey.threshold, payload["threshold"])

    @data(
        {},
        "answers",
    )
    def test_create_survey_no_answers_or_wrong_type(self, answers: Any) -> None:
        payload = {"answers": answers, "sector": "Some Sector", "threshold": 3}

        response = self.client.post(self.URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"answers": ["Answers must be non-empty dictionary object!"]})

        self.assertEqual(Survey.objects.count(), 0)

    def test_create_survey_invalid_question(self) -> None:
        payload = {"answers": {"": "A"}, "sector": "Some Sector", "threshold": 3}

        response = self.client.post(self.URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"answers": ["Question cannot be empty!"]})

    def test_create_survey_invalid_answers(self) -> None:
        payload = {"answers": {"Q1": "C"}, "sector": "Some Sector", "threshold": 3}

        response = self.client.post(self.URL, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"answers": ["Answer must be one of the following values: A or B!"]})
