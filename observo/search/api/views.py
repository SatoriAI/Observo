from rest_framework import generics, permissions

from search.api.serializers import MatchSerializer, NotificationSerializer, WebsiteSerializer
from search.models import Match, Notification, Website


class CreateWebsiteView(generics.CreateAPIView):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer
    permission_classes = [
        permissions.AllowAny,
    ]


class WebsiteRetrieveView(generics.RetrieveAPIView):
    queryset = Website.objects.all()
    serializer_class = WebsiteSerializer
    permission_classes = [
        permissions.AllowAny,
    ]
    lookup_field = "pk"


class CreateMatchView(generics.CreateAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    permission_classes = [
        permissions.AllowAny,
    ]


class MatchRetrieveView(generics.RetrieveAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    permission_classes = [
        permissions.AllowAny,
    ]
    lookup_field = "pk"


class NotificationCreateView(generics.CreateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [
        permissions.AllowAny,
    ]
