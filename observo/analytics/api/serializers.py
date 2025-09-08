from rest_framework import serializers

from analytics.enums import PossibleAnswers
from analytics.models import Contact, Meeting, Survey
from analytics.utils.functions import hash_ip
from utils.clients import CalendlyClient


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = "__all__"
        read_only_fields = (
            "id",
            "email",
            "start",
            "finish",
            "name",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data: dict[str, str]) -> Meeting:
        uri = validated_data["uri"]
        invitee_uri = validated_data["invitee_uri"]

        calendly_client = CalendlyClient(uri=uri, invitee_uri=invitee_uri)

        event = calendly_client.get_event()
        invitee = calendly_client.get_invitee()

        obj = Meeting.objects.create(
            survey=validated_data["survey"],
            uri=uri,
            invitee_uri=invitee_uri,
            # Invitee information
            email=invitee["email"],
            nickname=invitee["name"],
            firstname=invitee["firstname"],
            lastname=invitee["lastname"],
            timezone=invitee["timezone"],
            # Meeting information
            start=event["start_time"],
            finish=event["end_time"],
            name=event["name"],
        )

        return obj


class SurveySerializer(serializers.ModelSerializer):
    cost = serializers.CharField(write_only=True)

    class Meta:
        model = Survey
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    @staticmethod
    def validate_answers(value: dict[str, str]) -> dict[str, str]:
        # Check whether incoming data is a proper, non-empty dictionary
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("Answers must be non-empty dictionary object!")

        # Check the correctness of the questions and corresponding answers
        for question, answer in value.items():
            if not question.strip():
                raise serializers.ValidationError("Question cannot be empty!")
            if answer not in PossibleAnswers:
                raise serializers.ValidationError(
                    f"Answer must be one of the following values: {' or '.join([a.value for a in PossibleAnswers])}!"
                )

        return value

    def create(self, validated_data: dict[str, str]) -> Survey:
        request = self.context.get("request")

        # Extract data from user's request
        user_agent = request.META.get("HTTP_USER_AGENT")
        referrer = request.META.get("HTTP_REFERER")
        client_ip = request.META.get("REMOTE_ADDR") or request.META.get("HTTP_X_FORWARDED_FOR").split(",")[0].strip()

        obj = Survey.objects.create(
            answers=validated_data["answers"],
            sector=validated_data.get("sector"),
            website=validated_data.get("website"),
            eager_to_pay=False if validated_data.get("cost") == PossibleAnswers.ANSWER_A else True,
            locale=validated_data.get("locale"),
            user_agent=user_agent,
            referrer=referrer,
            client_ip_hash=hash_ip(client_ip),
        )

        return obj


class AvailableDataSerializer(serializers.Serializer):
    sectors = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    locales = serializers.ListField(child=serializers.CharField(), allow_empty=True)
