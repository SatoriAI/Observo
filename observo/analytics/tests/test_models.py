import faker
from ddt import data, ddt, unpack
from django.test import TestCase

from analytics.models import Contact, Meeting, Survey
from analytics.tests.factories import MeetingFactory, SurveyFactory

fake = faker.Faker()


@ddt
class TestSurvey(TestCase):
    def test_create_survey_success(self) -> None:
        survey = Survey.objects.create(answers={"1": "A", "2": "B", "3": "C"})
        self.assertEqual(Survey.objects.count(), 1)
        self.assertEqual(str(survey), f"Survey #{survey.pk} (b=1/3)")

    @unpack
    @data(
        ({}, 0),
        ({"1": "A", "2": "B", "3": "C"}, 3),
    )
    def test_total_questions(self, answers: dict, expected: int) -> None:
        survey = Survey.objects.create(answers=answers)
        self.assertEqual(survey.total_questions, expected)

    @unpack
    @data(
        ({}, 0),
        ({"1": "A", "2": "A"}, 0),
        ({"1": "A", "2": "B", "3": "B"}, 2),
    )
    def test_b_count(self, answers: dict, expected: int) -> None:
        survey = Survey.objects.create(answers=answers)
        self.assertEqual(survey.b_count, expected)


class TestContact(TestCase):
    def setUp(self):
        self.email = fake.email()

    def test_create_contact_success(self) -> None:
        contact = Contact.objects.create(survey=SurveyFactory(), email=self.email)
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(str(contact), f"Contact #{contact.pk} left by {self.email}")


class TestMeeting(TestCase):
    def setUp(self):
        self.email = fake.email()

    def test_create_meeting_success(self) -> None:
        meeting = Meeting.objects.create(
            survey=SurveyFactory(),
            uri=fake.uri(),
            invitee_uri=fake.uri(),
            email=self.email,
            start=fake.date(),
            finish=fake.date(),
        )
        self.assertEqual(Meeting.objects.count(), 1)
        self.assertEqual(str(meeting), f"Meeting #{meeting.pk} with {self.email}")

    def test_identifier(self) -> None:
        uuid = fake.uuid4()
        meeting = MeetingFactory(uri=f"https://api.calendly.com/scheduled_events/{uuid}")
        self.assertEqual(meeting.identifier, uuid)
