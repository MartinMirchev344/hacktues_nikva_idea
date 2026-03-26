from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RecognitionHealthSerializer
from .services import get_recognition_service


class RecognitionHealthView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        service = get_recognition_service()
        serializer = RecognitionHealthSerializer(service.health())
        return Response(serializer.data)

