import factory
from factory.django import DjangoModelFactory

from analytics.models import Meeting, Survey


class SurveyFactory(DjangoModelFactory):
    class Meta:
        model = Survey

    locale = factory.Faker("locale")
    client_ip_hash = factory.Faker("ipv4")


class MeetingFactory(DjangoModelFactory):
    class Meta:
        model = Meeting

    survey = factory.SubFactory(SurveyFactory)

    uri = factory.Faker("uri")
    invitee_uri = factory.Faker("uri")

    email = factory.Faker("email")
    start = factory.Faker("date_time")
    finish = factory.Faker("date_time")
    name = factory.Faker("company")


__all__ = [
    "SurveyFactory",
    "MeetingFactory",
]
