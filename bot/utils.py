import re

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
