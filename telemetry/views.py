from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from stream.services import publish

from .models import BiomassRecord, TelemetryLog
from .serializers import BiomassRecordSerializer, TelemetryLogSerializer


def _level(status_text: str) -> str:
    """Map the AI status text (IDEAL / PERINGATAN / SANGAT BAIK) to a UI level."""
    head = status_text.upper()
    if head.startswith("PERINGATAN"):
        return "warning"
    if head.startswith("SANGAT BAIK"):
        return "good"
    return "ok"


def _to_stream_payload(data: dict) -> dict:
    """Same shape the AI sends to /ws/ingest/ (see CLAUDE.md payload contract)."""
    return {
        "timestamp": data["timestamp"],
        "count": data["catfish_count"],
        "telemetry": {
            "ph": data["ph"],
            "temp": data["temperature"],
            "turbidity": data["turbidity"],
            "tds": data["tds"],
        },
        "status": data["status"],
        "recommendation": data["recommendation"],
        "level": _level(data["status"]),
    }


@api_view(["GET", "POST"])
def telemetry_list(request):
    if request.method == "GET":
        logs = TelemetryLog.objects.all()[:50]  # 50 data terakhir
        return Response(TelemetryLogSerializer(logs, many=True).data)

    serializer = TelemetryLogSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        # Push to connected dashboards so they don't have to poll.
        async_to_sync(publish)(_to_stream_payload(serializer.data))
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def latest_telemetry(request):
    latest = TelemetryLog.objects.first()
    if latest:
        return Response(TelemetryLogSerializer(latest).data)
    return Response({}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET", "POST"])
def biomass_list(request):
    if request.method == "GET":
        records = BiomassRecord.objects.all()[:50]
        return Response(BiomassRecordSerializer(records, many=True).data)

    serializer = BiomassRecordSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def latest_biomass(request):
    latest = BiomassRecord.objects.first()
    if latest:
        return Response(BiomassRecordSerializer(latest).data)
    # 200 + {} (not 404): the dashboard polls this every 2s before the engine
    # has recorded anything, and a 404 spams logs / the browser console.
    return Response({})
