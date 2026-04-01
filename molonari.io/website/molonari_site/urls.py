from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("data/", include("data_viewer.urls")),
    path("", include("pages.urls")),
]
