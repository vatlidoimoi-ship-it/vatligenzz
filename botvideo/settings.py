import os
import re
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / ".runtime_data" / "video" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = BASE_DIR / ".runtime_data" / "video" / "cache"
AUDIO_CACHE_DIR = CACHE_DIR / "audio"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(BASE_DIR / ".env", override=False)
VIDEO_SIZE = (1280, 720)
JOB_ID_RE = re.compile(r"^[0-9a-f]{10}$")
DESIGN_TEMPLATES = {
    "studio": {
        "name": "Studio xanh",
        "description": "Sạch, sáng, hợp bài giảng phổ thông.",
        "bg": "#F3F4F6",
        "card": "#FFFFFF",
        "primary": "#2B4C7E",
        "accent": "#3AAFA9",
        "accent_light": "#DEF2F1",
        "text": "#1F2937",
        "muted": "#6B7280",
        "formula_bg": "#F7FBFB",
        "border": "#DEF2F1",
    },
    "chalkboard": {
        "name": "Bảng phấn",
        "description": "Nền xanh đậm, chữ sáng, cảm giác lớp học.",
        "bg": "#163832",
        "card": "#214D45",
        "primary": "#F8FAE5",
        "accent": "#F2C94C",
        "accent_light": "#2F6A60",
        "text": "#F4F7EA",
        "muted": "#C9D8CF",
        "formula_bg": "#173B35",
        "border": "#5AA897",
    },
    "notebook": {
        "name": "Vở ghi",
        "description": "Nhẹ nhàng, giống trang vở học sinh.",
        "bg": "#EEF2FF",
        "card": "#FFFDF7",
        "primary": "#1D4ED8",
        "accent": "#EF4444",
        "accent_light": "#DBEAFE",
        "text": "#1E293B",
        "muted": "#64748B",
        "formula_bg": "#FEF3C7",
        "border": "#BFDBFE",
    },
    "warm": {
        "name": "Warm Focus",
        "description": "Ấm, dễ nhìn cho video giải thích chậm.",
        "bg": "#F6F1EA",
        "card": "#FFF8EF",
        "primary": "#7C2D12",
        "accent": "#0F766E",
        "accent_light": "#CCFBF1",
        "text": "#292524",
        "muted": "#78716C",
        "formula_bg": "#FFEDD5",
        "border": "#FED7AA",
    },
    "neon": {
        "name": "Dark Neon",
        "description": "Tương phản mạnh, hợp video ngắn hiện đại.",
        "bg": "#0B1020",
        "card": "#111827",
        "primary": "#E0F2FE",
        "accent": "#22D3EE",
        "accent_light": "#164E63",
        "text": "#E5E7EB",
        "muted": "#94A3B8",
        "formula_bg": "#172554",
        "border": "#2563EB",
    },
    "history_archive": {
        "name": "Hồ sơ tư liệu",
        "description": "Giấy sáng, đỏ gạch và vàng đất cho bài sự kiện/văn kiện.",
        "bg": "#F7F1E6",
        "card": "#FFFDF8",
        "primary": "#203047",
        "accent": "#B23A2F",
        "accent_light": "#F4DFB8",
        "text": "#273241",
        "muted": "#756A5D",
        "formula_bg": "#FBF1DC",
        "border": "#D8C6AA",
    },
    "history_timeline": {
        "name": "Timeline hiện đại",
        "description": "Mốc thời gian rõ, sáng, hợp diễn biến theo giai đoạn.",
        "bg": "#F3F7F5",
        "card": "#FFFFFF",
        "primary": "#16324F",
        "accent": "#D99A2B",
        "accent_light": "#E8F3EF",
        "text": "#1F2937",
        "muted": "#64706B",
        "formula_bg": "#FFF7E4",
        "border": "#C8DDD6",
    },
    "history_strategy": {
        "name": "Bảng chiến lược",
        "description": "Sơ đồ node, mũi tên, hợp nguyên nhân-kết quả và phong trào.",
        "bg": "#182536",
        "card": "#223249",
        "primary": "#F8FAFC",
        "accent": "#E2B24C",
        "accent_light": "#30465E",
        "text": "#F1F5F9",
        "muted": "#B8C3CF",
        "formula_bg": "#263A52",
        "border": "#46627D",
    },
    "history_biography": {
        "name": "Kể chuyện nhân vật",
        "description": "Ấm, có điểm nhấn chân dung cho bài nhân vật lịch sử.",
        "bg": "#F6EEE2",
        "card": "#FFF9EF",
        "primary": "#24324A",
        "accent": "#9E3F2F",
        "accent_light": "#F1D8BE",
        "text": "#2C2A27",
        "muted": "#79695A",
        "formula_bg": "#FBEAD2",
        "border": "#DEC2A3",
    },
    "history_exam": {
        "name": "Ôn thi nhanh",
        "description": "Tương phản cao, bullet ngắn, nhấn đáp án và từ khóa.",
        "bg": "#F8FAFC",
        "card": "#FFFFFF",
        "primary": "#102A43",
        "accent": "#C2410C",
        "accent_light": "#FFEDD5",
        "text": "#172033",
        "muted": "#5B6573",
        "formula_bg": "#E0F2FE",
        "border": "#CBD5E1",
    },
    "history_newspaper_1990": {
        "name": "Báo tư liệu 1990",
        "description": "Giấy báo ngà, headline đậm, ảnh tư liệu và infographic kiểu báo cũ.",
        "bg": "#E8D8AF",
        "card": "#FFF4D2",
        "primary": "#1F1A17",
        "accent": "#B23A2F",
        "accent_light": "#E6C879",
        "text": "#27211D",
        "muted": "#6F6254",
        "formula_bg": "#F6E7BC",
        "border": "#B9A77F",
    },
}

def get_design_template(template_id):
    template_id = str(template_id or "studio")
    return DESIGN_TEMPLATES.get(template_id, DESIGN_TEMPLATES["studio"])

def mask_secret(value):
    value = str(value or "")
    return f"{value[:6]}...{value[-4:]}" if len(value) > 12 else "***"

def env_int(name, default, min_value=None, max_value=None):
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    if min_value is not None:
        value = max(min_value, value)
    if max_value is not None:
        value = min(max_value, value)
    return value

def is_valid_job_id(job_id):
    return bool(JOB_ID_RE.fullmatch(str(job_id or "")))
