import json
import shutil
import subprocess
from pathlib import Path

def media_duration_seconds(path):
    """Return media duration with ffprobe, or None when ffmpeg tools are unavailable."""
    ffprobe_bin = shutil.which("ffprobe")
    if not ffprobe_bin or not Path(path).exists():
        return None
    try:
        result = subprocess.run(
            [
                ffprobe_bin,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        duration = float((result.stdout or "").strip())
        return duration if duration > 0 else None
    except Exception as e:
        print(f"Duration probe error for {path}: {e}")
        return None

def parse_probe_float(value):
    try:
        number = float(value)
        return number if number > 0 else None
    except (TypeError, ValueError):
        return None

def probe_media_info(path):
    """Return format/video/audio durations so render can detect silent MP4 failures."""
    ffprobe_bin = shutil.which("ffprobe")
    media_path = Path(path)
    empty = {
        "exists": media_path.exists(),
        "duration": None,
        "video_duration": None,
        "audio_duration": None,
        "has_audio": False,
    }
    if not ffprobe_bin or not media_path.exists():
        return empty

    try:
        result = subprocess.run(
            [
                ffprobe_bin,
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type,duration",
                "-of",
                "json",
                str(media_path),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        data = json.loads(result.stdout or "{}")
    except Exception as e:
        print(f"Media probe error for {path}: {e}")
        return empty

    format_duration = parse_probe_float((data.get("format") or {}).get("duration"))
    info = {**empty, "duration": format_duration}
    for stream in data.get("streams") or []:
        codec_type = stream.get("codec_type")
        stream_duration = parse_probe_float(stream.get("duration")) or format_duration
        if codec_type == "video" and not info["video_duration"]:
            info["video_duration"] = stream_duration
        if codec_type == "audio" and not info["audio_duration"]:
            info["audio_duration"] = stream_duration
            info["has_audio"] = True
    return info

def media_audio_duration_seconds(path):
    return probe_media_info(path).get("audio_duration")

def media_duration_mismatch(info):
    video_duration = info.get("video_duration") or info.get("duration")
    audio_duration = info.get("audio_duration")
    if not video_duration or not audio_duration:
        return None
    return abs(video_duration - audio_duration)

def is_audio_video_mismatch(info):
    mismatch = media_duration_mismatch(info)
    video_duration = info.get("video_duration") or info.get("duration") or 0
    if mismatch is None:
        return False
    return mismatch > max(2.0, video_duration * 0.03)

def normalize_scene_video(ffmpeg_bin, input_path, output_path):
    """Normalize generated scenes to CFR 25fps before final concat."""
    result = subprocess.run(
        [
            ffmpeg_bin,
            "-y",
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-c:v",
            "libx264",
            "-threads",
            "1",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-r",
            "25",
            "-fps_mode",
            "cfr",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=900,
    )
    if result.returncode != 0 or not Path(output_path).exists():
        print(f"Normalize scene failed for {input_path}: {(result.stderr or '')[-800:]}")
        return False
    return True

def concat_scene_videos(ffmpeg_bin, job_dir, scene_files, output_path, suffix="", reencode=False):
    concat_list_path = job_dir / f"concat{suffix}.txt"
    concat_content = "\n".join([f"file '{p.name}'" for p in scene_files])
    concat_list_path.write_text(concat_content, encoding="ascii")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-fflags",
        "+genpts",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list_path),
    ]
    if reencode:
        cmd.extend([
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-pix_fmt",
            "yuv420p",
        ])
    else:
        cmd.extend(["-c", "copy"])
    cmd.extend(["-movflags", "+faststart", str(output_path)])
    cmd[-1:-1] = ['-threads', '1']
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=900)
    return {
        "ok": result.returncode == 0 and output_path.exists(),
        "concat_list": concat_list_path.name,
        "stderr_tail": (result.stderr or "")[-1200:],
    }
