import os
import django
import re
import sys

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")  # change!
django.setup()

from bot.models import MusicFile

CLEAN_RE = re.compile(r"""
    (\[.*?\]) |          # [DIYDOR.NET], [MuzFm.UZ]
    (\(.*?\)) |          # (dodasi.com)
    (@\w+) |             # @fayzfmuzbot
    (www\.\S+) |         # www.fayzfm.uz
    (https?://\S+)       # links
""", re.VERBOSE)


def clean_text(text):
    if not text:
        return text
    cleaned = CLEAN_RE.sub("", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def run():
    total = MusicFile.objects.count()
    updated = 0

    for i, mf in enumerate(MusicFile.objects.iterator(), start=1):
        new_file_name = clean_text(mf.file_name)
        new_performer = clean_text(mf.performer)
        new_title = clean_text(mf.title)

        if (
            new_file_name != mf.file_name
            or new_performer != mf.performer
            or new_title != mf.title
        ):
            mf.file_name = new_file_name
            mf.performer = new_performer
            mf.title = new_title
            mf.save(update_fields=["file_name", "performer", "title"])
            updated += 1

        # Print dynamic progress (every row, overwrite line)
        percent = (i / total) * 100
        sys.stdout.write(
            f"\r🔄 Processing {i}/{total} ({percent:.2f}%) | ✅ Updated: {updated}"
        )
        sys.stdout.flush()

    print(f"\n🎉 Done! Cleaned {updated} out of {total} records.")


if __name__ == "__main__":
    run()
