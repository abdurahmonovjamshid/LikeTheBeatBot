from django.contrib import admin
from .models import TgUser, MusicFile


@admin.register(TgUser)
class TgUserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "first_name", "last_name", "username", "phone", "is_bot", "deleted", "created_at")
    search_fields = ("telegram_id", "first_name", "last_name", "username", "phone")
    list_filter = ("is_bot", "deleted", "language_code")
    readonly_fields = ("created_at",)


@admin.register(MusicFile)
class MusicFileAdmin(admin.ModelAdmin):
    list_display = ("id", "performer", "title", "file_name", "source_channel", "created_at")
    search_fields = ("performer", "title", "file_name", "caption")
    list_filter = ("source_channel", "created_at")
    ordering = ("-created_at",)

    def get_display_name(self, obj):
        if obj.performer and obj.title:
            return f"{obj.performer} – {obj.title}"
        return obj.file_name or obj.file_id
    get_display_name.short_description = "Track"

