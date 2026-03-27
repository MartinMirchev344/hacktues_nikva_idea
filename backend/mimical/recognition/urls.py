from django.urls import path

from .views import AlphabetPredictView, RecognitionHealthView

urlpatterns = [
    path('health/', RecognitionHealthView.as_view(), name='recognition-health'),
    path('alphabet/predict/', AlphabetPredictView.as_view(), name='alphabet-predict'),
]

