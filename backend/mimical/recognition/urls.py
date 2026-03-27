from django.urls import path

from .views import RecognitionHealthView


urlpatterns = [
    path("health/", RecognitionHealthView.as_view(), name="recognition-health"),
]

