from django.contrib import admin

from .models import AppRelease


@admin.register(AppRelease)
class AppReleaseAdmin(admin.ModelAdmin):
    list_display = ('platform', 'version_name', 'version_code', 'is_active', 'released_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('version_name', 'version_code', 'release_notes')
    ordering = ('-version_code',)
