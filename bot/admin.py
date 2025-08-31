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
    list_display = (
        "id",
        "track_display",
        "size_mb_display",
        "duration_display",
        "source_channel",
        "created_at",
    )
    search_fields = ("performer", "title", "file_name")
    list_filter = ("source_channel", "created_at")
    ordering = ("-created_at",)

    def track_display(self, obj):
        """Show performer + title or fallback to file_name"""
        if obj.performer and obj.title:
            return f"{obj.performer} – {obj.title}"
        return obj.file_name or obj.file_id
    track_display.short_description = "Track"


    def size_mb_display(self, obj):
        """Human-readable file size"""
        return obj.size_mb or "-"
    size_mb_display.short_description = "Size"

    def duration_display(self, obj):
        """Show duration mm:ss"""
        return obj.duration_min or "-"
    duration_display.short_description = "Duration"
