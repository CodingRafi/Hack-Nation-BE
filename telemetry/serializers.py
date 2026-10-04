from rest_framework import serializers

from .models import BiomassRecord, TelemetryLog


class TelemetryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemetryLog
        fields = "__all__"


class BiomassRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiomassRecord
        fields = "__all__"
