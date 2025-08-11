from rest_framework import generics, permissions

from analytics.api.serializers import ContactSerializer, SurveySerializer
from analytics.models import Contact, Survey


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
