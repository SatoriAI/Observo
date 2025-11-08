from django.core.signing import BadSignature, Signer
from django.db.models import Case, Count, Exists, IntegerField, OuterRef, Sum, When
from django.db.models.functions import TruncDay, TruncWeek
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from rest_framework import generics, permissions
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from analytics.api.filters import SurveyFilter
from analytics.api.serializers import AvailableDataSerializer, ContactSerializer, MeetingSerializer, SurveySerializer
from analytics.models import Contact, Meeting, Survey


@require_http_methods(["GET"])
def unsubscribe_contact(request, token: str):
    signer = Signer()
    try:
        contact_id = int(signer.unsign(token))
    except (BadSignature, ValueError):
        return HttpResponse("Invalid unsubscribe link.", status=400)

    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        return HttpResponse("Contact not found.", status=404)

    if contact.active_subscription:
        contact.active_subscription = False
        contact.save()

    return HttpResponse("You have been unsubscribed from future emails.")


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


class AvailableDataView(generics.GenericAPIView):
    queryset = Survey.objects.all()
    serializer_class = AvailableDataSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()

        sectors_qs = (
            qs.exclude(sector__isnull=True).exclude(sector="").order_by().values_list("sector", flat=True).distinct()
        )
        locales_qs = (
            qs.exclude(locale__isnull=True).exclude(locale="").order_by().values_list("locale", flat=True).distinct()
        )

        data = {
            "sectors": sorted(sectors_qs),
            "locales": sorted(locales_qs),
        }

        serializer = self.get_serializer(instance=data)

        return Response(serializer.data)


class AnalyticsOverviewView(ListAPIView):
    queryset = Survey.objects.all()
    filterset_class = SurveyFilter
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]

    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.annotate(
            has_meeting=Exists(Meeting.objects.filter(survey_id=OuterRef("pk"))),
            has_contact=Exists(Contact.objects.filter(survey_id=OuterRef("pk"))),
            show_up=Exists(Meeting.objects.filter(survey_id=OuterRef("pk"), appeared=True)),
        )

        return qs

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        # Totals & funnel
        totals = qs.aggregate(
            total_surveys=Count("id"),
            surveys_with_meeting=Sum(Case(When(has_meeting=True, then=1), default=0, output_field=IntegerField())),
            contacts_left=Sum(Case(When(has_contact=True, then=1), default=0, output_field=IntegerField())),
            show_ups=Sum(Case(When(show_up=True, then=1), default=0, output_field=IntegerField())),
        )
        totals["surveys_without_meeting"] = (totals["total_surveys"] or 0) - (totals["surveys_with_meeting"] or 0)
        totals["no_shows"] = (totals["surveys_with_meeting"] or 0) - (totals["show_ups"] or 0)
        totals["conversion_rate"] = (
            (totals["surveys_with_meeting"] or 0) / totals["total_surveys"] if totals["total_surveys"] else 0
        )
        totals["show_up_rate"] = (totals["show_ups"] or 0) / (totals["surveys_with_meeting"] or 1)

        # Time series
        group_by = request.query_params.get("group_by", "day")
        trunc = TruncWeek("created_at") if group_by == "week" else TruncDay("created_at")

        surveys_series = qs.annotate(dt=trunc).values("dt").annotate(count=Count("id")).order_by("dt")

        meetings_series = (
            Meeting.objects.filter(survey_id__in=qs.values("id"))
            .annotate(dt=trunc)
            .values("dt")
            .annotate(count=Count("id"))
            .order_by("dt")
        )

        # Breakdowns
        by_sector = (
            qs.values("sector")
            .annotate(
                surveys=Count("id"),
                with_meeting=Sum(Case(When(has_meeting=True, then=1), default=0, output_field=IntegerField())),
            )
            .order_by("-surveys")
        )
        for row in by_sector:
            row["conversion_rate"] = (row["with_meeting"] or 0) / row["surveys"] if row["surveys"] else 0

        by_locale = (
            qs.values("locale")
            .annotate(
                surveys=Count("id"),
                with_meeting=Sum(Case(When(has_meeting=True, then=1), default=0, output_field=IntegerField())),
            )
            .order_by("-surveys")
        )
        for row in by_locale:
            row["conversion_rate"] = (row["with_meeting"] or 0) / row["surveys"] if row["surveys"] else 0

        # Geolocation data
        geolocation_data = []
        for survey in qs.exclude(geolocation__isnull=True).exclude(geolocation=""):
            coordinates = survey.coordinates
            if coordinates:
                try:
                    latitude, longitude = coordinates
                    geolocation_data.append(
                        {
                            "latitude": float(latitude),
                            "longitude": float(longitude),
                        }
                    )
                except (ValueError, TypeError):
                    continue

        return Response(
            {
                "filters": {
                    "date_from": request.query_params.get("date_from"),
                    "date_to": request.query_params.get("date_to"),
                    "sector": request.query_params.get("sector"),
                    "locale": request.query_params.get("locale"),
                },
                "totals": totals,
                "time_series": {
                    "surveys": [{"date": r["dt"].date().isoformat(), "count": r["count"]} for r in surveys_series],
                    "meetings": [{"date": r["dt"].date().isoformat(), "count": r["count"]} for r in meetings_series],
                },
                "breakdowns": {
                    "by_sector": list(by_sector),
                    "by_locale": list(by_locale),
                },
                "geolocation": geolocation_data,
            }
        )
