import asyncio
import hashlib
import json
import os
import shutil
import threading
from pathlib import Path

from gtts import gTTS

from .settings import AUDIO_CACHE_DIR
from .media_tools import media_duration_seconds

tts_cache_locks = {}
tts_cache_locks_lock = threading.Lock()

def tts_cache_key(text, provider="gtts", lang="vi", voice="default", speed="1.0", rate="+0%", volume="+0%"):
    payload = json.dumps({
        "provider": provider,
        "lang": lang,
        "voice": voice,
        "speed": speed,
        "rate": rate,
        "volume": volume,
        "text": text,
    }, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def cache_lock_for(key):
    with tts_cache_locks_lock:
        lock = tts_cache_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            tts_cache_locks[key] = lock
        return lock


def edge_voice_for(voice, lang):
    if voice and voice != "default":
        return voice
    if str(lang or "").lower().startswith("vi"):
        return "vi-VN-HoaiMyNeural"
    return "en-US-AriaNeural"


def edge_rate_for(speed, rate):
    if rate:
        return rate
    try:
        speed_value = float(speed)
    except (TypeError, ValueError):
        return "+0%"
    percent = round((speed_value - 1.0) * 100)
    sign = "+" if percent >= 0 else ""
    return f"{sign}{percent}%"


async def save_edge_tts(text, output_path, voice, rate, volume):
    import edge_tts

    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, volume=volume)
    await communicate.save(str(output_path))


def generate_tts(text, output_path):
    """Generate speech audio file using the configured free/basic TTS provider."""
    clean_text = (text or "").strip()
    if not clean_text:
        clean_text = "Bước này không có lời thuyết minh."
    provider = os.getenv("TTS_PROVIDER", "edge").strip().lower() or "edge"
    if provider == "edge-tts":
        provider = "edge"
    lang = os.getenv("TTS_LANG", "vi").strip() or "vi"
    voice = os.getenv("TTS_VOICE", "default").strip() or "default"
    speed = os.getenv("TTS_SPEED", "1.0").strip() or "1.0"
    edge_voice = edge_voice_for(voice, lang)
    edge_rate = edge_rate_for(speed, os.getenv("TTS_EDGE_RATE", "").strip())
    edge_volume = os.getenv("TTS_EDGE_VOLUME", "+0%").strip() or "+0%"
    cache_voice = edge_voice if provider == "edge" else voice
    cache_rate = edge_rate if provider == "edge" else "+0%"
    cache_volume = edge_volume if provider == "edge" else "+0%"
    cache_enabled = os.getenv("TTS_CACHE", "1").strip().lower() not in {"0", "false", "off", "no"}
    cache_key = tts_cache_key(
        clean_text,
        provider=provider,
        lang=lang,
        voice=cache_voice,
        speed=speed,
        rate=cache_rate,
        volume=cache_volume,
    )
    cache_path = AUDIO_CACHE_DIR / f"{cache_key}.mp3"
    output_path = Path(output_path)

    if cache_enabled and cache_path.exists() and media_duration_seconds(cache_path):
        shutil.copy2(cache_path, output_path)
        return True, "cache"

    lock = cache_lock_for(cache_key)
    try:
        with lock:
            if cache_enabled and cache_path.exists() and media_duration_seconds(cache_path):
                shutil.copy2(cache_path, output_path)
                return True, "cache"

            temp_path = output_path.with_suffix(".tmp.mp3")
            if provider == "edge":
                async def bounded_save():
                    await asyncio.wait_for(save_edge_tts(clean_text, temp_path, edge_voice, edge_rate, edge_volume), timeout=90)
                asyncio.run(bounded_save())
            elif provider == "gtts":
                tts = gTTS(text=clean_text, lang=lang, timeout=30)
                tts.save(str(temp_path))
            else:
                raise RuntimeError(f"TTS provider '{provider}' chưa được hỗ trợ.")
            if not media_duration_seconds(temp_path):
                raise RuntimeError("TTS trả về file không có âm thanh hợp lệ.")
            if cache_enabled:
                cache_temp = cache_path.with_suffix(".tmp.mp3")
                shutil.copy2(temp_path, cache_temp)
                os.replace(cache_temp, cache_path)
            shutil.move(str(temp_path), output_path)
            return True, provider
    except Exception as e:
        print(f"TTS error for '{clean_text}': {e}")
        return False, "error"
