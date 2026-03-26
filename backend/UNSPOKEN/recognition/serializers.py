from rest_framework import serializers


class RecognitionHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    model_ready = serializers.BooleanField()
    dependencies_ready = serializers.BooleanField()
    supported_lessons = serializers.ListField(child=serializers.IntegerField())
    configured_model = serializers.CharField()
    configured_variant = serializers.CharField()
    cache_dir = serializers.CharField()
    warnings = serializers.ListField(child=serializers.CharField())

