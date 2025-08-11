from rest_framework import serializers

from analytics.enums import PossibleAnswers
from analytics.models import Contact, Survey
from analytics.utils.functions import hash_ip


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = "__all__"
        read_only_fields = (
            "id",
            "total_questions",
            "b_count",
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
                raise serializers.ValidationError("Answer must be one of the following values: 'A' or 'B'!")

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
            locale=validated_data.get("locale"),
            threshold=validated_data.get("threshold"),
            user_agent=user_agent,
            referrer=referrer,
            client_ip_hash=hash_ip(client_ip),
        )

        return obj
