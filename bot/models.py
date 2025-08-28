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

    source_channel = models.CharField(max_length=255)
    source_message_id = models.BigIntegerField()
    mirrored_message_id = models.BigIntegerField()  # message_id in dest channel

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name or self.title or self.file_id

