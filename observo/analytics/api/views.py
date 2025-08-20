from rest_framework import generics, permissions

from analytics.api.serializers import ContactSerializer, MeetingSerializer, SurveySerializer
from analytics.models import Contact, Meeting, Survey


class SurveyCreateView(generics.CreateAPIView):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [
        permissions.AllowAny,
    ]


class ContactCreateView(generics.CreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [
        permissions.AllowAny,
    ]


class CreateMeetingView(generics.CreateAPIView):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = [
        permissions.AllowAny,
    ]
