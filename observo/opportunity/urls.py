from django.urls import path

from opportunity.api.views import opportunity_summary_pdf

app_name = "opportunity"

urlpatterns = [
    path("opportunities/<uuid:pk>/summary/", opportunity_summary_pdf, name="api-opportunity-summary"),
]
