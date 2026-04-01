from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("hardware/", views.hardware, name="hardware"),
    path("software/", views.software, name="software"),
    path("contact/", views.contact, name="contact"),
]
