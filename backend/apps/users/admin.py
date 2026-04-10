from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import LumiqUser


@admin.register(LumiqUser)
class LumiqUserAdmin(UserAdmin):
    list_display = ['email', 'full_name', 'company', 'role', 'is_onboarded', 'created_at']
    list_filter = ['role', 'is_onboarded', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'company']
    ordering = ['-created_at']

    fieldsets = UserAdmin.fieldsets + (
        ('Lumiq', {
            'fields': ('company', 'role', 'avatar_url', 'is_onboarded')
        }),
    )