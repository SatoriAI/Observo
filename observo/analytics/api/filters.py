import django_filters

from analytics.models import Survey


class SurveyFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    sector = django_filters.CharFilter(field_name="sector", lookup_expr="iexact")
    locale = django_filters.CharFilter(field_name="locale", lookup_expr="iexact")

    class Meta:
        model = Survey
        fields = [
            "sector",
            "locale",
            "date_from",
            "date_to",
        ]
