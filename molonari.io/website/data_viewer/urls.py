from django.urls import path

from . import views

app_name = "data_viewer"

urlpatterns = [
    path("", views.sensor_data, name="sensor_data"),
]
