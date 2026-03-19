from django.contrib import admin
from .models import UserProfile, VerificationToken


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'country', 'created_at']
    list_filter = ['country', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'city']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'profile_image', 'phone', 'date_of_birth')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'zip_code', 'country')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VerificationToken)
class VerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'verified', 'created_at', 'expires_at']
    list_filter = ['verified', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['token', 'created_at']
