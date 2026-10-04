from django.contrib import admin

from .models import BiomassRecord, TelemetryLog

admin.site.register(TelemetryLog)
admin.site.register(BiomassRecord)
