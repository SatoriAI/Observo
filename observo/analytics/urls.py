from django.urls import path

from analytics.api.views import (
    AnalyticsOverviewView,
    AvailableDataView,
    ContactCreateView,
    CreateMeetingView,
    SurveyCreateView,
    unsubscribe_contact,
)

app_name = "analytics"

urlpatterns = [
    path("surveys/", SurveyCreateView.as_view(), name="api-surveys-create"),
    path("contacts/", ContactCreateView.as_view(), name="api-contacts-create"),
    path("meetings/", CreateMeetingView.as_view(), name="api-meetings-create"),
    path("data/", AvailableDataView.as_view(), name="api-available-data"),
    path("analytics/", AnalyticsOverviewView.as_view(), name="api-analytics-overview"),
    path("unsubscribe/<str:token>/", unsubscribe_contact, name="unsubscribe"),
]
