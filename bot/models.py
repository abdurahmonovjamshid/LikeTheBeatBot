from django.db import models

class TgUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=15, default='-')

    is_bot = models.BooleanField(default=False)
    language_code = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Joined')

    deleted = models.BooleanField(default=False)

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name or ''}".strip()
        return (full_name[:30] + '...') if len(full_name) > 30 else full_name


class MusicFile(models.Model):
    file_id = models.CharField(max_length=255, unique=True)
    file_name = models.CharField(max_length=512, blank=True, null=True)
    performer = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    caption = models.TextField(blank=True, null=True)

    duration = models.PositiveIntegerField(blank=True, null=True)  # in seconds
    file_size = models.BigIntegerField(blank=True, null=True)  # in bytes

    source_channel = models.CharField(max_length=255)
    source_message_id = models.BigIntegerField()
    mirrored_message_id = models.BigIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name or self.title or self.file_id

    @property
    def duration_min(self):
        """Return duration formatted as mm:ss"""
        if self.duration:
            mins, secs = divmod(self.duration, 60)
            return f"{mins}:{secs:02d}"
        return None

    @property
    def size_mb(self):
        """Return file size in MB"""
        if self.file_size:
            return f"{self.file_size / (1024*1024):.2f} MB"
        return None


