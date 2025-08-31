import re
from django.db.models import Q
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.models import MusicFile

RANGE_RE = re.compile(r"https?://t\.me/([^/\s]+)/(\d+)\s*-\s*https?://t\.me/\1/(\d+)", re.I)
LINK_RE  = re.compile(r"https?://t\.me/([^/\s]+)/(\d+)", re.I)

def parse_range(text: str):
    """
    Accepts: 'https://t.me/chan/100 - https://t.me/chan/200'
    Returns: ('@chan', 100, 200)  (normalized order)
    """
    m = RANGE_RE.search(text)
    if not m:
        # Fallback: parse two links, also ensure same channel
        links = LINK_RE.findall(text)
        if len(links) != 2 or links[0][0] != links[1][0]:
            return None, None, None
        chan, a, b = links[0][0], int(links[0][1]), int(links[1][1])
    else:
        chan, a, b = m.group(1), int(m.group(2)), int(m.group(3))

    if a > b:
        a, b = b, a
    return f"@{chan}", a, b


AUDIO_EXTS = (".mp3", ".m4a", ".flac", ".wav", ".ogg", ".oga", ".opus")

def is_music_message(msg) -> tuple[str|None, str|None]:
    """
    Returns (file_id, file_name) if audio/music, else (None, None).
    """
    if not msg:
        return None, None

    if getattr(msg, "audio", None):
        return msg.audio.file_id, getattr(msg.audio, "file_name", None)

    doc = getattr(msg, "document", None)
    if doc:
        mt = (doc.mime_type or "").lower()
        fn = (doc.file_name or "")
        if mt.startswith("audio") or fn.lower().endswith(AUDIO_EXTS):
            return doc.file_id, fn

    return None, None


PAGE_SIZE = 10

def format_results(query, items, total, page):
    start_num = (page - 1) * PAGE_SIZE + 1
    end_num = start_num + len(items) - 1

    header = f"🔍 {query}\nResults {start_num}-{end_num} of {total}\n\n"
    lines = []

    for idx, item in enumerate(items, start=start_num):
        performer = item.performer or ""
        title = item.title or item.file_name or "Unknown"
        duration = item.duration_min or ""
        size = item.size_mb or ""
        bitrate = f"{int((item.file_size or 0) * 8 / (item.duration or 1) / 1000)}k" if item.duration else ""

        text = f"{idx}. {performer} – {title} {duration} {size} {bitrate}"
        lines.append(text)

    return header + "\n".join(lines)

def search_music(query, page=1):
    # search in file_name, performer, title
    qs = MusicFile.objects.filter(
        Q(file_name__icontains=query) |
        Q(performer__icontains=query) |
        Q(title__icontains=query)
    ).order_by('-created_at')

    total = qs.count()
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    items = qs[start:end]

    return items, total

def make_keyboard(query, page, total):
    markup = InlineKeyboardMarkup(row_width=5)
    buttons = []

    # numbers (1–10)
    for i in range(1, PAGE_SIZE+1):
        buttons.append(InlineKeyboardButton(str(i), callback_data=f"play:{query}:{page}:{i}"))

    markup.add(*buttons)

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"page:{query}:{page-1}"))
    nav.append(InlineKeyboardButton("❌", callback_data="close"))
    if page * PAGE_SIZE < total:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"page:{query}:{page+1}"))

    markup.add(*nav)
    return markup
