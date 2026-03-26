from rest_framework import serializers

from .models import Attempt, Exercise, Lesson


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = [
            "id",
            "lesson",
            "title",
            "exercise_type",
            "prompt",
            "instructions",
            "expected_sign",
            "order",
            "repetitions_target",
            "passing_score",
            "target_pose_data",
            "target_motion_data",
        ]
        read_only_fields = ["id"]


class LessonListSerializer(serializers.ModelSerializer):
    exercise_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "difficulty",
            "sign_language",
            "estimated_duration_minutes",
            "is_published",
            "exercise_count",
        ]
        read_only_fields = ["id", "slug"]


class LessonDetailSerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "difficulty",
            "sign_language",
            "estimated_duration_minutes",
            "is_published",
            "exercises",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class AttemptSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Attempt
        fields = [
            "id",
            "user",
            "exercise",
            "status",
            "score",
            "accuracy_score",
            "speed_score",
            "handshape_score",
            "detected_sign",
            "coach_summary",
            "feedback_items",
            "tracking_data",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "started_at",
            "created_at",
            "updated_at",
        ]


class AttemptCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = [
            "id",
            "exercise",
            "status",
            "score",
            "accuracy_score",
            "speed_score",
            "handshape_score",
            "detected_sign",
            "coach_summary",
            "feedback_items",
            "tracking_data",
            "completed_at",
        ]
        read_only_fields = ["id"]
