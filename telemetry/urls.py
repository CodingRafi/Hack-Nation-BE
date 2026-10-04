from django.urls import path

from . import views

urlpatterns = [
    path("telemetry/", views.telemetry_list, name="telemetry-list"),
    path("telemetry/latest/", views.latest_telemetry, name="telemetry-latest"),
    path("biomass/", views.biomass_list, name="biomass-list"),
    path("biomass/latest/", views.latest_biomass, name="biomass-latest"),
]
