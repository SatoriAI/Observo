from django.urls import path

from search.api.views import (
    CreateMatchView,
    CreateWebsiteView,
    MatchRetrieveView,
    NotificationCreateView,
    WebsiteRetrieveView,
)

app_name = "search"

urlpatterns = [
    path("website/", CreateWebsiteView.as_view(), name="api-website-create"),
    path("website/<int:pk>/", WebsiteRetrieveView.as_view(), name="api-website-detail"),
    path("match/", CreateMatchView.as_view(), name="api-match-create"),
    path("match/<int:pk>/", MatchRetrieveView.as_view(), name="api-match-detail"),
    path("notification/", NotificationCreateView.as_view(), name="api-notification-create"),
]
