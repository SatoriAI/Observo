from django.urls import path

from analytics.api.views import ContactCreateView, CreateMeetingView, SurveyCreateView

app_name = "analytics"

urlpatterns = [
    path("surveys/", SurveyCreateView.as_view(), name="api-surveys-create"),
    path("contacts/", ContactCreateView.as_view(), name="api-contacts-create"),
    path("meetings/", CreateMeetingView.as_view(), name="api-meetings-create"),
]
