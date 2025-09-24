from rest_framework import generics, permissions

from search.api.serializers import WebsiteSerializer
from search.models import Website


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
