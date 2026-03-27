from django.contrib import admin
from .models import Lesson, Exercise, Attempt, UserLessonProgress


class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 1


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'sign_language', 'difficulty', 'is_published', 'estimated_duration_minutes')
    list_filter = ('sign_language', 'difficulty', 'is_published')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ExerciseInline]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'exercise_type', 'expected_sign', 'order', 'passing_score')
    list_filter = ('exercise_type', 'lesson__sign_language')
    search_fields = ('title', 'expected_sign')


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'exercise', 'status', 'score', 'accuracy_score', 'handshape_score', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'exercise__expected_sign', 'detected_sign')


@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'is_completed', 'best_score', 'attempts_count')
