from django.urls import path

from search.api.views import (
    CreateWebsiteView,
    WebsiteRetrieveView,
)

app_name = "search"

urlpatterns = [
    path("website/", CreateWebsiteView.as_view(), name="api-website-create"),
    path("website/<int:pk>/", WebsiteRetrieveView.as_view(), name="api-website-detail"),
]
