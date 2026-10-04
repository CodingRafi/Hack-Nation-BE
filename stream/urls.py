from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health),
    path("latest/", views.latest),
    path("ingest/", views.ingest),
]
