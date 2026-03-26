from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'xp', 'streak', 'last_activity_date', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Game Stats', {'fields': ('xp', 'streak', 'last_activity_date', 'avatar_url')}),
    )
