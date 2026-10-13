import base64
import importlib.util
import json
import math
import mimetypes
import os
import re
import shutil
import subprocess
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from functools import lru_cache
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from .visual_design import physics_svg, polish_html, slide_markup

from .media_tools import (
    concat_scene_videos,
    is_audio_video_mismatch,
    media_audio_duration_seconds,
    media_duration_mismatch,
    media_duration_seconds,
    normalize_scene_video,
    probe_media_info,
)
from .settings import (
    AUDIO_CACHE_DIR,
    BASE_DIR,
    CACHE_DIR,
    DESIGN_TEMPLATES,
    JOB_ID_RE,
    MEDIA_DIR,
    VIDEO_SIZE,
    env_int,
    get_design_template,
    is_valid_job_id,
    mask_secret,
)
from .tts import generate_tts

jobs = {}
jobs_lock = threading.Lock()

PHYSICS_SUBJECT_ALIASES = {
    "vật lý",
    "vật lí",
    "vat ly",
    "vat li",
    "cơ học",
    "co hoc",
    "điện học",
    "dien hoc",
    "quang học",
    "quang hoc",
    "sóng và dao động",
    "song va dao dong",
    "nhiệt học",
    "nhiet hoc",
}

HISTORY_SUBJECT_ALIASES = {
    "lịch sử",
    "lich su",
    "sử",
    "su",
    "lịch sử việt nam",
    "lich su viet nam",
    "lịch sử thế giới",
    "lich su the gioi",
}


def normalize_subject(subject):
    value = re.sub(r"\s+", " ", str(subject or "").strip())
    if not value:
        return "Toán học"
    lowered = value.lower()
    if lowered in PHYSICS_SUBJECT_ALIASES:
        return "Vật lý"
    if lowered in HISTORY_SUBJECT_ALIASES:
        return "Lịch sử"
    return value


def is_physics_subject(subject):
    return normalize_subject(subject) == "Vật lý"


def is_history_subject(subject):
    return normalize_subject(subject) == "Lịch sử"


def subject_branch(subject):
    if is_physics_subject(subject):
        return "physics"
    if is_history_subject(subject):
        return "history"
    return "math"



def demo_script(problem, subject):
    """Return a predictable script when Gemini is not configured or on error."""
    problem = (problem or "").strip() or "Cho tam giác ABC vuông tại A, AB=3, AC=4. Tính BC."
    subject = normalize_subject(subject)
    if is_history_subject(subject):
        return {
            "problem": problem,
            "subject": "Lịch sử",
            "lesson_title": "Hệ thống hóa chủ đề lịch sử",
            "design_template": "history_newspaper_1990",
            "history_style": "history_newspaper_1990",
            "steps": [
                {
                    "title": "Mở hồ sơ sự kiện",
                    "narration": "Mình sẽ không bắt các em học vẹt một đoạn dài. Ta mở chủ đề này như một hồ sơ lịch sử: trước hết xác định mốc thời gian, bối cảnh, lực lượng chính và câu hỏi đề đang nhắm tới.",
                    "slide_text": "Chủ đề\n- Mốc thời gian\n- Bối cảnh\n- Nhân vật/lực lượng\n- Yêu cầu cần trả lời",
                    "latex": None,
                    "geometry": None,
                    "diagram": None,
                    "visual": {
                        "type": "document_card",
                        "title": "Hồ sơ chủ đề",
                        "items": ["Mốc thời gian", "Bối cảnh", "Nhân vật/lực lượng", "Yêu cầu đề bài"],
                    },
                },
                {
                    "title": "Diễn biến chính",
                    "narration": "Ta xếp các sự kiện theo trục thời gian. Cách này giúp nhìn ra logic trước sau, thay vì nhớ từng ý như một danh sách rời rạc.",
                    "slide_text": "Diễn biến\n- Bối cảnh hình thành\n- Sự kiện chính\n- Bước ngoặt\n- Kết quả",
                    "latex": None,
                    "geometry": None,
                    "diagram": None,
                    "visual": {
                        "type": "timeline",
                        "events": [
                            {"date": "Bối cảnh", "label": "Điều kiện xuất hiện"},
                            {"date": "Sự kiện", "label": "Diễn biến chính"},
                            {"date": "Bước ngoặt", "label": "Điểm quyết định"},
                            {"date": "Kết quả", "label": "Tác động cuối"},
                        ],
                    },
                },
                {
                    "title": "Logic nguyên nhân - kết quả",
                    "narration": "Phần ăn điểm thường nằm ở chuỗi nguyên nhân dẫn đến diễn biến, rồi diễn biến tạo ra kết quả và ý nghĩa. Nhớ được chuỗi này thì bài viết sẽ có xương sống.",
                    "slide_text": "Logic cần nhớ\nNguyên nhân → Diễn biến → Kết quả → Ý nghĩa",
                    "latex": None,
                    "geometry": None,
                    "diagram": None,
                    "visual": {
                        "type": "cause_event_result",
                        "nodes": [
                            {"label": "Nguyên nhân", "text": "Vì sao xảy ra?"},
                            {"label": "Diễn biến", "text": "Xảy ra thế nào?"},
                            {"label": "Kết quả", "text": "Dẫn tới điều gì?"},
                            {"label": "Ý nghĩa", "text": "Tác động ra sao?"},
                        ],
                    },
                },
                {
                    "title": "Tóm tắt ghi nhớ",
                    "narration": "Chốt lại, đừng ôm quá nhiều chữ. Hãy giữ vài từ khóa mấu chốt: mốc thời gian, bối cảnh, diễn biến trọng tâm, kết quả và ý nghĩa.",
                    "slide_text": "Cần nhớ\n1. Mốc thời gian\n2. Bối cảnh\n3. Diễn biến trọng tâm\n4. Kết quả\n5. Ý nghĩa",
                    "latex": None,
                    "geometry": None,
                    "diagram": None,
                    "visual": {"type": "memory_summary", "items": ["Mốc thời gian", "Bối cảnh", "Diễn biến", "Kết quả", "Ý nghĩa"]},
                },
            ],
            "summary": ["Mốc thời gian", "Bối cảnh", "Diễn biến", "Kết quả", "Ý nghĩa"],
        }
    if is_physics_subject(subject):
        lower_problem = problem.lower()
        if any(token in lower_problem for token in ["mạch", "mach", "điện", "dien", "hiệu điện thế", "hieu dien the", "điện trở", "dien tro", "dòng điện", "dong dien"]):
            return {
                "problem": problem,
                "subject": "Vật lý",
                "lesson_title": "Giải bài tập điện học",
                "steps": [
                    {
                        "title": "Đọc dữ kiện điện học",
                        "narration": "Ta xác định hiệu điện thế, điện trở và đại lượng cần tìm là cường độ dòng điện trong mạch.",
                        "latex": "U = 12\\,\\text{V} \\\\ R = 6\\,\\Omega",
                        "geometry": None,
                        "diagram": {"type": "circuit", "labels": {"U": "U = 12 V", "R": "R = 6 Ω"}},
                    },
                    {
                        "title": "Áp dụng định luật Ôm",
                        "narration": "Với đoạn mạch chỉ có điện trở, cường độ dòng điện được tính bằng hiệu điện thế chia cho điện trở.",
                        "latex": "I = \\frac{U}{R}",
                        "geometry": None,
                        "diagram": {"type": "circuit", "labels": {"U": "U", "R": "R", "I": "I"}},
                    },
                    {
                        "title": "Thay số và kết luận",
                        "narration": "Thay U bằng 12 vôn và R bằng 6 ôm, ta được cường độ dòng điện bằng 2 ampe.",
                        "latex": "I = \\frac{12}{6} = 2\\,\\text{A}",
                        "geometry": None,
                        "diagram": {"type": "circuit", "labels": {"I": "I = 2 A"}},
                    },
                ],
                "summary": ["I = 2 A"],
            }
        return {
            "problem": problem if problem else "Một vật khối lượng 2 kg chịu lực kéo 10 N. Bỏ qua ma sát. Tính gia tốc của vật.",
            "subject": "Vật lý",
            "lesson_title": "Giải bài tập cơ học",
            "steps": [
                {
                    "title": "Đọc dữ kiện vật lí",
                    "narration": "Ta xác định các đại lượng đã biết: khối lượng của vật là 2 ki lô gam, lực tác dụng là 10 niutơn, và bỏ qua ma sát.",
                    "latex": "m = 2\\,\\text{kg} \\\\ F = 10\\,\\text{N}",
                    "geometry": None,
                    "diagram": {"type": "force", "labels": {"mass": "m = 2 kg", "force": "F = 10 N"}},
                },
                {
                    "title": "Chọn công thức",
                    "narration": "Vì vật chịu lực tổng hợp theo phương chuyển động, ta dùng định luật hai Newton để liên hệ lực, khối lượng và gia tốc.",
                    "latex": "F = ma \\\\ a = \\frac{F}{m}",
                    "geometry": None,
                    "diagram": {"type": "force", "labels": {"force": "F", "acceleration": "a"}},
                },
                {
                    "title": "Thay số và tính",
                    "narration": "Thay lực bằng 10 niutơn và khối lượng bằng 2 ki lô gam, ta được gia tốc bằng 5 mét trên giây bình phương.",
                    "latex": "a = \\frac{10}{2} = 5\\,\\text{m/s}^2",
                    "geometry": None,
                    "diagram": {"type": "motion", "labels": {"acceleration": "a = 5 m/s^2"}},
                },
                {
                    "title": "Kết luận",
                    "narration": "Vậy gia tốc của vật là 5 mét trên giây bình phương.",
                    "latex": "a = 5\\,\\text{m/s}^2",
                    "geometry": None,
                    "diagram": {"type": "motion", "labels": {"result": "a = 5 m/s^2"}},
                },
            ],
            "summary": ["a = 5 m/s^2"],
        }
    if "tam giác" in problem.lower() or subject == "Hình học":
        return {
            "problem": problem,
            "subject": subject,
            "steps": [
                {
                    "title": "Đọc dữ kiện bài toán",
                    "narration": "Ta xác định các dữ kiện quan trọng: Tam giác ABC vuông tại A, có độ dài hai cạnh góc vuông AB bằng 3 và AC bằng 4.",
                    "latex": "AB = 3, \\quad AC = 4, \\quad \\widehat{A} = 90^\\circ",
                    "geometry": {"points": {"A": [0, 0], "B": [3, 0], "C": [0, 4]}},
                },
                {
                    "title": "Áp dụng định lý Pythagoras",
                    "narration": "Vì tam giác ABC vuông tại A, theo định lý Pythagoras ta có bình phương cạnh huyền BC bằng tổng bình phương hai cạnh góc vuông.",
                    "latex": "BC^2 = AB^2 + AC^2",
                    "geometry": None,
                },
                {
                    "title": "Tính toán kết quả",
                    "narration": "Thay số vào công thức: BC bình phương bằng 3 bình phương cộng 4 bình phương bằng 25. Từ đó tính được cạnh BC bằng 5.",
                    "latex": "BC = \\sqrt{3^2 + 4^2} = \\sqrt{25} = 5",
                    "geometry": None,
                },
            ],
        }
    return {
        "problem": problem,
        "subject": subject,
        "steps": [
            {
                "title": "Phân tích đề bài",
                "narration": "Ta đọc kỹ đề bài và trích xuất các thông số chính cùng yêu cầu bài toán.",
                "latex": None,
                "geometry": None,
            },
            {
                "title": "Lập luận & Thay số",
                "narration": "Ta áp dụng công thức phù hợp, thay các dữ kiện đã biết vào biểu thức để tính toán.",
                "latex": "x = a + b",
                "geometry": None,
            },
            {
                "title": "Kết luận",
                "narration": "Sau khi tính toán cẩn thận, ta ghi lại đáp số chính xác của bài toán.",
                "latex": None,
                "geometry": None,
            },
        ],
    }


def circle_diameter_tangent_script(problem):
    geometry = infer_circle_geometry_from_text(problem)
    if not geometry:
        return None
    return {
        "problem": problem,
        "lesson_title": "Chứng minh hình học đường tròn",
        "steps": [
            {
                "title": "Dựng hình và nhận dạng giả thiết",
                "narration": "Ta xét đường tròn tâm O có AB là đường kính, C nằm trên cung AB. Các đường thẳng tại A, B và C là các tiếp tuyến tương ứng, tạo nên các điểm F, E và D như đề bài.",
                "latex": "A,O,B \\text{ thẳng hàng} \\\\ C \\in (O) \\\\ CD, BE, AF \\text{ là các tiếp tuyến}",
                "geometry": geometry,
            },
            {
                "title": "Đưa bài toán về mô hình tọa độ",
                "narration": "Đặt O làm gốc, bán kính bằng 1, A có tọa độ (-1;0), B có tọa độ (1;0), và C có tọa độ (u;v) với u bình phương cộng v bình phương bằng 1.",
                "latex": "A(-1;0) \\\\ B(1;0) \\\\ C(u;v),\\quad u^2+v^2=1",
                "geometry": geometry,
            },
            {
                "title": "Tìm các điểm D, E, F",
                "narration": "Tiếp tuyến tại C có phương trình ux cộng vy bằng 1. Từ đó D nằm trên AB nên có tọa độ (1/u;0). Tiếp tuyến tại B là x bằng 1, tiếp tuyến tại A là x bằng -1, suy ra tọa độ E và F.",
                "latex": "D\\left(\\frac{1}{u};0\\right) \\\\ E\\left(1;\\frac{2v}{1+u}\\right) \\\\ F\\left(-1;\\frac{2v}{1-u}\\right)",
                "geometry": geometry,
            },
            {
                "title": "Chứng minh DE bằng DF",
                "narration": "Tính bình phương hai độ dài DE và DF từ các tọa độ vừa tìm được. Sau khi rút gọn bằng hệ thức u bình phương cộng v bình phương bằng 1, hai biểu thức bằng nhau.",
                "latex": "DE^2 = DF^2 \\\\ \\Rightarrow DE = DF",
                "geometry": geometry,
            },
            {
                "title": "Chứng minh CD là đường trung trực của EF",
                "narration": "Từ DE bằng DF suy ra D nằm trên đường trung trực của EF. Đồng thời theo phương trình tiếp tuyến tại C và tọa độ E, F, ta kiểm tra được CD vuông góc EF. Vì vậy CD chính là đường trung trực của EF.",
                "latex": "DE = DF \\\\ CD \\perp EF \\\\ \\Rightarrow CD \\text{ là đường trung trực của } EF",
                "geometry": geometry,
            },
            {
                "title": "Kết luận",
                "narration": "Vậy ta đã chứng minh được DE bằng DF và đường thẳng CD là đường trung trực của đoạn EF.",
                "latex": "DE = DF \\\\ CD \\perp EF",
                "geometry": geometry,
            },
        ],
        "summary": [
            "DE = DF",
            "CD là đường trung trực của EF",
        ],
    }


def rule_based_script_from_problem(problem, subject):
    problem = str(problem or "").strip()
    if not problem:
        return None
    circle_script = circle_diameter_tangent_script(problem)
    if circle_script:
        return circle_script
    return None










def gemini_api_keys():
    raw_values = [
        os.getenv("GEMINI_API_KEY", ""),
        os.getenv("GEMINI_API_KEYS", ""),
    ]
    keys = []
    seen = set()
    for raw in raw_values:
        for key in re.findall(r"AIza[0-9A-Za-z_\-]{35}", raw):
            if key not in seen:
                seen.add(key)
                keys.append(key)
        for key in re.split(r"[\s,;]+", raw.strip()):
            if key.startswith("AIza") and key not in seen:
                seen.add(key)
                keys.append(key)
    order = []
    for raw_index in re.split(r"[\s,;]+", os.getenv("GEMINI_KEY_ORDER", "").strip()):
        if not raw_index:
            continue
        try:
            index = int(raw_index) - 1
        except ValueError:
            continue
        if 0 <= index < len(keys) and index not in order:
            order.append(index)
    if order:
        ordered_keys = [keys[index] for index in order]
        ordered_keys.extend(key for index, key in enumerate(keys) if index not in order)
        keys = ordered_keys
    return keys


def gemini_model_candidates():
    raw_models = [
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        os.getenv("GEMINI_FALLBACK_MODELS", ""),
    ]
    models = []
    seen = set()
    for raw in raw_models:
        for model in re.split(r"[\s,;]+", str(raw or "").strip()):
            if model and model not in seen:
                seen.add(model)
                models.append(model)
    return models or ["gemini-3.5-flash"]


def gemini_image_model_candidates():
    raw_models = [
        os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.6-flash"),
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        os.getenv("GEMINI_FALLBACK_MODELS", ""),
    ]
    models = []
    seen = set()
    for raw in raw_models:
        for model in re.split(r"[\s,;]+", str(raw or "").strip()):
            if model and model not in seen:
                seen.add(model)
                models.append(model)
    return models or gemini_model_candidates()


def allow_demo_fallback():
    return os.getenv("ALLOW_DEMO_FALLBACK", "0").strip().lower() in {"1", "true", "yes", "on"}


def is_default_demo_script(script):
    problem = str((script or {}).get("problem") or "").lower()
    joined_steps = " ".join(
        f"{step.get('title', '')} {step.get('narration', '')} {step.get('latex', '')}"
        for step in ((script or {}).get("steps") or [])
        if isinstance(step, dict)
    ).lower()
    return (
        "ab=3" in problem
        and "ac=4" in problem
        and "tính bc" in problem
        and ("pythagoras" in joined_steps or "bc^2" in joined_steps)
    )


def extract_problem_text_from_image(image_path, api_keys, models=None, subject="Toán học"):
    if not image_path or not Path(image_path).exists():
        return ""
    subject = normalize_subject(subject)
    ocr_timeout = env_int("GEMINI_OCR_TIMEOUT", 35, 10, 90)
    max_keys = env_int("GEMINI_OCR_MAX_KEYS", 3, 1, len(api_keys))
    models = models or gemini_image_model_candidates()
    prompt = f"""
    Đọc chính xác nội dung đề bài môn {subject} trong ảnh và trả về JSON thuần.
    Không giải bài. Không thêm nhận xét.
    Giữ nguyên các ký hiệu quan trọng như O, A, B, C, D, E, F, AB, AC, BC, DE = DF, m, F, a, v, U, I, R, P và đơn vị kg, N, m/s, m/s^2, V, A, Ω.
    Nếu ảnh có phần "Chứng minh rằng", phải chép đủ các mệnh đề cần chứng minh.
    Schema:
    {{"problem":"nội dung đề trong ảnh"}}
    """
    last_error = None
    attempted = 0
    for model in models:
        for api_key in api_keys[:max_keys]:
            attempted += 1
            try:
                data = gemini_generate_json(api_key, model, prompt, image_path=image_path, timeout=ocr_timeout)
                problem = re.sub(r"\s+", " ", str(data.get("problem") or "")).strip()
                if len(problem) >= 20:
                    return problem
                last_error = RuntimeError("OCR trả về nội dung quá ngắn.")
            except Exception as error:
                last_error = error
                message = str(error).replace(api_key, "[MASKED_KEY]")
                print(f"Gemini OCR error with {model} {mask_secret(api_key)}: {message[:500]}")
    print(f"Gemini OCR failed after {attempted} attempt(s). Last error: {last_error}")
    return ""

def gemini_generate_json(api_key, model, text_prompt, image_path=None, timeout=75):
    parts = []
    if image_path and Path(image_path).exists():
        mime_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
        data = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        parts.append({"inline_data": {"mime_type": mime_type, "data": data}})
    parts.append({"text": text_prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    curl_bin = shutil.which("curl.exe") or shutil.which("curl")
    if not curl_bin:
        raise RuntimeError("Không tìm thấy curl để gọi Gemini REST.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    result = subprocess.run(
        [
            curl_bin,
            "-sS",
            "--max-time",
            str(timeout),
            "-H",
            "Content-Type: application/json",
            "-H",
            f"x-goog-api-key: {api_key}",
            "--data-binary",
            "@-",
            url,
        ],
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=timeout + 10,
    )
    body = result.stdout or ""
    if result.returncode != 0:
        raise RuntimeError((result.stderr or body or f"curl exited {result.returncode}")[:1000])

    data = json.loads(body)
    if "error" in data:
        raise RuntimeError(json.dumps(data["error"], ensure_ascii=False)[:1000])

    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    if not text:
        raise RuntimeError("Gemini không trả nội dung text.")
    return json.loads(text)


def detect_subproblem_labels(text):
    labels = []
    for match in re.finditer(r"(?m)(?:^|\n|\r)\s*([a-d])\s*[\).]", str(text or "")):
        label = match.group(1).lower()
        if label not in labels:
            labels.append(label)
    return labels


def ensure_step_shape(step):
    return {
        "title": str(step.get("title") or "Bước giải").strip(),
        "narration": str(step.get("narration") or "").strip(),
        "slide_text": str(step.get("slide_text") or step.get("onscreen_text") or "").strip(),
        "latex": step.get("latex") or None,
        "geometry": step.get("geometry") if isinstance(step.get("geometry"), dict) else None,
        "diagram": step.get("diagram") if isinstance(step.get("diagram"), dict) else None,
        "visual": step.get("visual") if isinstance(step.get("visual"), dict) else None,
        "layout": step.get("layout") if isinstance(step.get("layout"), str) else None,
        "section_label": step.get("section_label") if isinstance(step.get("section_label"), str) else None,
        "image_ref": step.get("image_ref") if isinstance(step.get("image_ref"), str) else None,
        "image_caption": step.get("image_caption") if isinstance(step.get("image_caption"), str) else None,
    }


def normalize_latex_input(value):
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("$$", "$").strip("$").strip()
    text = re.sub(r"\\\\(?=[A-Za-z])", lambda _match: "\\", text)
    text = re.sub(r"\bvec\s*([A-Z]{2})\b", r"\\vec{\1}", text)
    text = re.sub(r"\bvec([A-Z]{2})\b", r"\\vec{\1}", text)
    text = text.replace("begincases", "\\begin{cases}").replace("endcases", "\\end{cases}")
    text = text.replace("\\dfrac", "\\frac")
    text = re.sub(r"(?<!\\)sqrt\s*\{", r"\\sqrt{", text)
    text = re.sub(r"(?<!\\)cdot\b", r"\\cdot", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def split_latex_display_lines(value):
    text = normalize_latex_input(value) or ""
    if not text:
        return []
    text = re.sub(r"\\\[(.*?)\\\]", r"\1", text).strip()
    text = re.sub(r"\\\((.*?)\\\)", r"\1", text).strip()
    lines = [
        line.strip()
        for line in re.split(r"\s*\\\\(?:\[[^\]]+\])?\s*", text)
        if line.strip()
    ]
    return lines or [text]


def latex_for_katex(value):
    text = normalize_latex_input(value) or ""
    if not text:
        return ""
    if "\\begin{aligned}" in text or "\\begin{gathered}" in text:
        return text
    if "\\\\" in text:
        return "\\begin{aligned} " + text + " \\end{aligned}"
    return text


def looks_like_geometry_problem(text):
    text = str(text or "").lower()
    return bool(extract_points_from_text(text)) or any(
        token in text
        for token in ["tam giác", "hình", "tọa độ", "vect", "vector", "đường tròn", "điểm"]
    )


def has_raw_latex_command(text):
    return bool(re.search(r"\\[A-Za-z]+|\$[^$]+\$|begincases|endcases|\bvec[A-Z]{2}\b", str(text or "")))


def infer_circle_geometry_from_text(text):
    source = str(text or "")
    lower = source.lower()
    if "đường tròn" not in lower:
        return None

    diameter_match = re.search(r"đường\s+kính\s+([A-Z])\s*([A-Z])", source, re.IGNORECASE)
    if not diameter_match:
        return None

    a_label = diameter_match.group(1).upper()
    b_label = diameter_match.group(2).upper()
    labels = set(re.findall(r"\b([A-Z])\b", source))
    c_label = "C" if "C" in labels else "C"
    o_label = "O" if "O" in labels else "O"
    d_label = "D" if "D" in labels else None
    e_label = "E" if "E" in labels else None
    f_label = "F" if "F" in labels else None

    # Schematic coordinates for a circle with AB as diameter. Extra points show
    # the standard tangent construction without relying on exact user coordinates.
    points = {
        o_label: [0.0, 0.0],
        a_label: [-1.0, 0.0],
        b_label: [1.0, 0.0],
        c_label: [0.38, 0.925],
    }
    if d_label:
        points[d_label] = [2.63, 0.0]
    if e_label:
        points[e_label] = [1.0, 1.38]
    if f_label:
        points[f_label] = [-1.0, 2.85]

    return {
        "type": "circle_diameter_tangent",
        "diameter": [a_label, b_label],
        "center": o_label,
        "points": points,
    }


def is_recap_step(step):
    title = str(step.get("title") or "").lower()
    return any(token in title for token in ["tổng quan", "tổng kết", "toàn bộ bài giải", "tóm tắt lời giải", "lưu ý kiểm tra"])


def is_full_solution_step(step):
    title = str(step.get("title") or "").lower()
    return "toàn bộ bài giải" in title or "tóm tắt lời giải" in title


def flatten_subproblems(script, subject=None):
    subject = normalize_subject(subject or script.get("subject"))
    subproblems = script.get("subproblems")
    if not isinstance(subproblems, list) or not subproblems:
        return script

    steps = []
    intro_parts = []
    for item_index, item in enumerate(subproblems, start=1):
        label = str(item.get("label") or "").strip()
        question = str(item.get("question") or "").strip()
        if label or question:
            if is_history_subject(subject):
                intro_parts.append(f"Phần {item_index}: {question or label}".strip())
            else:
                intro_parts.append(f"{label}) {question}".strip())

    if intro_parts:
        if is_history_subject(subject):
            intro_narration = "Chủ đề lịch sử này có các ý cần hệ thống lần lượt: " + "; ".join(intro_parts)
        elif is_physics_subject(subject):
            intro_narration = "Bài Vật lí có các ý cần phân tích lần lượt: " + "; ".join(intro_parts)
        else:
            intro_narration = "Bài toán có các ý cần giải lần lượt: " + "; ".join(intro_parts)
        steps.append({
            "title": "Tổng quan đề bài",
            "narration": intro_narration,
            "latex": None,
            "geometry": None,
            "diagram": None,
            "visual": None,
        })

    summary = []
    for item_index, item in enumerate(subproblems, start=1):
        label = str(item.get("label") or "").strip()
        question = str(item.get("question") or "").strip()
        if is_history_subject(subject):
            section_title = f"Phần {item_index}"
            section_label = f"Phần {item_index}"
        else:
            section_title = f"Ý {label}" if label else "Một ý của bài"
            section_label = section_title
        raw_item_steps = item.get("steps") if isinstance(item.get("steps"), list) else []
        if question and not (is_history_subject(subject) and raw_item_steps):
            if is_history_subject(subject):
                section_narration = f"Ta bắt đầu hệ thống {section_title.lower()}: {question}"
            elif is_physics_subject(subject):
                section_narration = f"Ta bắt đầu phân tích {section_title.lower()}: {question}"
            else:
                section_narration = f"Ta bắt đầu giải {section_title.lower()}: {question}"
            steps.append({
                "title": section_title,
                "narration": section_narration,
                "section_label": section_label,
                "latex": None,
                "geometry": item.get("geometry") if isinstance(item.get("geometry"), dict) else None,
                "diagram": item.get("diagram") if isinstance(item.get("diagram"), dict) else None,
                "visual": item.get("visual") if isinstance(item.get("visual"), dict) else None,
            })

        for raw_step in item.get("steps") or []:
            step = ensure_step_shape(raw_step)
            step["section_label"] = section_label
            if is_history_subject(subject) and not step["title"].lower().startswith(section_title.lower()):
                step["title"] = f"{section_title} - {step['title']}"
            elif label and not step["title"].lower().startswith(f"ý {label}".lower()):
                step["title"] = f"Ý {label} - {step['title']}"
            steps.append(step)

        final_answer = str(item.get("final_answer") or "").strip()
        if final_answer:
            final_latex = None if is_history_subject(subject) else item.get("final_latex") or None
            if is_history_subject(subject):
                final_narration = final_answer if final_answer.lower().startswith(("kết luận", "ý nghĩa")) else f"Kết luận: {final_answer}"
            else:
                final_narration = final_answer if final_answer.lower().startswith(("vậy", "kết luận")) else f"Vậy {final_answer}"
            steps.append({
                "title": f"Kết lại phần {item_index}" if is_history_subject(subject) else f"Kết luận ý {label}" if label else "Kết luận",
                "narration": final_narration,
                "section_label": section_label,
                "latex": final_latex,
                "geometry": None,
                "diagram": None if is_history_subject(subject) else item.get("diagram") if isinstance(item.get("diagram"), dict) else None,
                "visual": item.get("visual") if isinstance(item.get("visual"), dict) else None,
            })
            summary.append(f"{label}) {final_answer}".strip())

    raw_summary = script.get("summary")
    if isinstance(raw_summary, list):
        summary.extend(str(item).strip() for item in raw_summary if str(item).strip())

    unique_summary = []
    seen_summary_labels = set()
    for item in summary:
        label_match = re.match(r"\s*([a-d])\s*[\).]", item, re.IGNORECASE)
        if label_match:
            label = label_match.group(1).lower()
            if label in seen_summary_labels:
                continue
            seen_summary_labels.add(label)
        if item not in unique_summary:
            unique_summary.append(item)
    if unique_summary:
        steps.append({
            "title": "Tổng kết chủ đề" if is_history_subject(subject) else "Tổng kết đáp án",
            "narration": "Tổng kết: " + "; ".join(unique_summary),
            "latex": None,
            "geometry": None,
            "diagram": None,
            "visual": None,
        })

    script["steps"] = steps
    if is_history_subject(subject):
        script = enrich_history_from_problem(script, subject)
    elif is_physics_subject(subject):
        script = enrich_physics_from_problem(script, subject)
    else:
        script = enrich_geometry_from_problem(script)
    return script


def ensure_script_quality(script, original_problem="", subject=None):
    subject = normalize_subject(subject or (script.get("subject") if isinstance(script, dict) else None))
    if not isinstance(script, dict):
        raise ValueError("AI không trả về kịch bản JSON hợp lệ.")

    script = flatten_subproblems(script, subject)
    script["subject"] = subject
    if original_problem and not script.get("problem"):
        script["problem"] = original_problem
    if original_problem and original_problem not in str(script.get("problem") or ""):
        script["_input_problem"] = original_problem
    script = enrich_geometry_from_problem(script)
    script = enrich_physics_from_problem(script, subject)
    steps = [ensure_step_shape(step) for step in script.get("steps") or []]
    script["steps"] = steps

    labels = detect_subproblem_labels(original_problem)
    has_summary = any("tổng kết" in step["title"].lower() or "kết luận" in step["title"].lower() for step in steps)
    has_each_label = all(
        any(f"ý {label}" in step["title"].lower() or f"{label})" in step["narration"].lower() for step in steps)
        for label in labels
    )

    if labels and not has_each_label:
        missing = ", ".join(label for label in labels if not any(f"ý {label}" in step["title"].lower() for step in steps))
        steps.insert(0, {
            "title": "Lưu ý kiểm tra kịch bản",
            "narration": f"Đề bài có nhiều ý. Hệ thống phát hiện kịch bản cần được kiểm tra thêm cho các ý: {missing}.",
            "latex": None,
            "geometry": None,
        })

    if not has_summary:
        final_lines = []
        for step in steps[-4:]:
            text = step["narration"].strip()
            if text:
                final_lines.append(text)
        steps.append({
            "title": "Tổng kết chủ đề" if is_history_subject(subject) else "Tổng kết đáp án",
            "narration": "Tổng kết chủ đề: " + " ".join(final_lines[-2:]) if is_history_subject(subject) and final_lines else "Tổng kết lời giải: " + " ".join(final_lines[-2:]) if final_lines else "Tổng kết lại các ý chính của chủ đề." if is_history_subject(subject) else "Tổng kết lại các kết quả chính của bài toán.",
            "latex": None,
            "geometry": None,
        })

    min_steps = 4 if not labels else max(6, len(labels) * 3 + 1)
    script["steps"] = steps
    script = enrich_geometry_from_problem(script)
    steps = script.get("steps") or []
    script["quality"] = {
        "detected_subproblems": labels,
        "has_summary": True,
        "expected_min_steps": min_steps,
        "actual_steps": len(steps),
    }
    return sanitize_script_for_render(script, original_problem=original_problem, subject=subject)


def sanitize_script_for_render(script, original_problem="", subject=None):
    subject = normalize_subject(subject or (script.get("subject") if isinstance(script, dict) else None))
    history_subject = is_history_subject(subject)
    physics_subject = is_physics_subject(subject)
    if not isinstance(script, dict):
        raise ValueError("Kịch bản phải là một đối tượng JSON hợp lệ.")
    script["subject"] = subject

    warnings = []
    quality = script.get("quality") if isinstance(script.get("quality"), dict) else {}
    existing_warnings = quality.get("warnings") if isinstance(quality.get("warnings"), list) else []
    warnings.extend(str(item) for item in existing_warnings if str(item).strip())

    if original_problem and not script.get("problem"):
        script["problem"] = original_problem
    if original_problem and original_problem not in str(script.get("problem") or ""):
        script["_input_problem"] = original_problem

    steps = [ensure_step_shape(step) for step in script.get("steps") or []]
    if not steps:
        raise ValueError("Kịch bản không có bước giảng; không thể thay bằng đề demo.")

    sanitized_steps = []
    for index, step in enumerate(steps, start=1):
        if history_subject:
            step["subject"] = "Lịch sử"
            section_label = step.get("section_label") or f"Phần {index}"
            step["section_label"] = section_label
            step["title"] = clean_history_title(step.get("title"), index)
        original_narration = step.get("narration") or ""
        cleaned_narration = narration_display_text(original_narration)
        if not cleaned_narration:
            cleaned_narration = "Phần này cần được kiểm tra lại nội dung." if history_subject else "Bước này cần được kiểm tra lại nội dung lời giải."
            warnings.append(f"Step {index} thiếu lời thuyết minh, đã thêm lời nhắc kiểm tra.")
        elif cleaned_narration != original_narration:
            if has_raw_latex_command(original_narration):
                warnings.append(f"Step {index} có LaTeX trong lời thuyết minh, đã chuyển sang dạng hiển thị.")
            if "\n" in cleaned_narration and "\n" not in str(original_narration):
                warnings.append(f"Step {index} đã được tự xuống dòng theo từng ý.")
        if history_subject:
            cleaned_narration = restore_history_text(cleaned_narration)
        step["narration"] = cleaned_narration

        if history_subject:
            if step.get("latex"):
                warnings.append(f"Step {index} thuộc Lịch sử nên đã bỏ trường LaTeX không phù hợp.")
            step["latex"] = None
            step["geometry"] = None
            step["diagram"] = None
        else:
            original_latex = step.get("latex")
            normalized_latex = normalize_latex_input(original_latex)
            if original_latex and normalized_latex != original_latex:
                warnings.append(f"Step {index} đã chuẩn hóa công thức LaTeX.")
            step["latex"] = normalized_latex

        original_slide_text = step.get("slide_text") or ""
        step["slide_text"] = build_history_slide_text(step) if history_subject else build_slide_text(step)
        if history_subject:
            step["slide_text"] = restore_history_text(step["slide_text"])
        if original_slide_text and step["slide_text"] != narration_display_text(original_slide_text):
            warnings.append(f"Step {index} đã rút gọn chữ hiển thị trên slide.")
        elif not original_slide_text and step["slide_text"] != cleaned_narration:
            warnings.append(f"Step {index} đã tách lời đọc và chữ hiển thị trên slide.")

        if history_subject and len(step["slide_text"]) > 520:
            warnings.append(f"Phần {index} khá dài, renderer sẽ tự tách thành nhiều scene nhỏ để tránh tràn chữ.")
        if len(cleaned_narration) > 420:
            warnings.append(f"Step {index} dài, renderer sẽ tự tách thành nhiều scene con.")
        sanitized_steps.append(step)

    if history_subject and len(sanitized_steps) > 1:
        before_count = len(sanitized_steps)
        sanitized_steps = [step for step in sanitized_steps if not is_history_transition_step(step)]
        removed_count = before_count - len(sanitized_steps)
        if removed_count:
            warnings.append(f"Đã bỏ {removed_count} slide chuyển đoạn Lịch sử quá ngắn để video không bị loãng nội dung.")

    script["steps"] = sanitized_steps
    if history_subject:
        script = enrich_history_from_problem(script, subject)
    elif physics_subject:
        script = enrich_physics_from_problem(script, subject)
    else:
        script = enrich_geometry_from_problem(script)

    problem_text = f"{script.get('problem') or ''} {script.get('_input_problem') or ''} {original_problem or ''}"
    if is_physics_subject(subject) and looks_like_geometry_problem(problem_text):
        model_used = str(script.get("_model_used") or "").lower()
        if "geometry" in model_used or isinstance(script.get("detected_geometry"), dict):
            subject = "Hình học"
            script["subject"] = subject
            script = strip_physics_diagrams(script)
            warnings.append("Script hình học từng bị nhận nhầm là Vật lí, đã dọn diagram Vật lí trước khi render.")

    if looks_like_geometry_problem(problem_text):
        missing_geometry = [
            index for index, step in enumerate(script.get("steps") or [], start=1)
            if not step.get("geometry")
        ]
        if missing_geometry and extract_points_from_text(problem_text):
            warnings.append("Bài hình/tọa độ đã được tự gắn hình minh họa từ các điểm trong đề.")

    if looks_like_physics_problem(problem_text, subject):
        missing_diagram = [
            index for index, step in enumerate(script.get("steps") or [], start=1)
            if not step.get("diagram")
        ]
        script = enrich_physics_from_problem(script, subject)
        if missing_diagram:
            warnings.append("Bài Vật lí đã được tự gắn sơ đồ minh họa bên phải cho các bước thiếu diagram.")

    if is_history_subject(subject):
        missing_visual = [
            index for index, step in enumerate(script.get("steps") or [], start=1)
            if not isinstance(step.get("visual"), dict)
        ]
        script = enrich_history_from_problem(script, subject)
        if missing_visual:
            warnings.append("Bai Lich su da duoc tu gan so do/timeline/the tom tat cho cac buoc thieu visual.")

    labels = detect_subproblem_labels(problem_text)
    if labels:
        has_summary = any("tổng kết" in str(step.get("title") or "").lower() for step in script.get("steps") or [])
        if not has_summary:
            summary_items = []
            for label in labels:
                conclusion = next(
                    (
                        step.get("narration")
                        for step in script.get("steps") or []
                        if f"ý {label}" in str(step.get("title") or "").lower()
                        and ("kết luận" in str(step.get("title") or "").lower() or str(step.get("narration") or "").lower().startswith("vậy"))
                    ),
                    "",
                )
                if conclusion:
                    summary_items.append(f"{label}) {conclusion}")
            if summary_items:
                script["steps"].append({
                    "title": "Tổng kết chủ đề" if history_subject else "Tổng kết đáp án",
                    "narration": narration_display_text("Tổng kết: " + "; ".join(summary_items)),
                    "latex": None,
                    "geometry": None,
                })
                warnings.append("Đề có nhiều ý nhưng thiếu tổng kết, đã thêm scene tổng kết.")

    script["steps"] = [step for step in script.get("steps") or [] if not is_full_solution_step(step)]
    if history_subject:
        script = enrich_history_from_problem(script, subject)
    elif physics_subject:
        script = enrich_physics_from_problem(script, subject)
    else:
        script = enrich_geometry_from_problem(script)
    if history_subject:
        added_full_solution = False
    else:
        script, added_full_solution = ensure_full_solution_slide(script)
    if added_full_solution:
        warnings.append("Đã thêm slide toàn bộ bài giải để người xem đọc lại mạch giải hoàn chỉnh.")
    if history_subject:
        for step in script.get("steps") or []:
            step["latex"] = None
            step["geometry"] = None
            step["diagram"] = None
        script = enrich_history_from_problem(script, subject)
    elif physics_subject:
        script = enrich_physics_from_problem(script, subject)
    else:
        script = enrich_geometry_from_problem(script)
    steps = script.get("steps") or []
    deduped_warnings = []
    for warning in warnings:
        if warning and warning not in deduped_warnings:
            deduped_warnings.append(warning)

    script["quality"] = {
        **quality,
        "detected_subproblems": quality.get("detected_subproblems") or labels,
        "has_summary": any("tổng kết" in str(step.get("title") or "").lower() or "kết luận" in str(step.get("title") or "").lower() for step in steps),
        "actual_steps": len(steps),
        "warnings": deduped_warnings[:20],
        "sanitized": True,
    }
    return script


def compact_solution_line(text, max_chars=180):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0].strip()
    return cut


def trim_display_line(text, max_chars=76):
    text = re.sub(r"\s+", " ", str(text or "")).strip(" -•\t")
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0].strip()


def wrap_display_text(text, max_chars=74):
    text = re.sub(r"\s+", " ", str(text or "")).strip(" -•\t")
    if not text:
        return []
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def is_history_filler_sentence(text):
    lower = normalized_asset_text(text)
    filler_tokens = [
        "chao cac em",
        "cac em co biet khong",
        "bay gio chung ta sang",
        "ta bat dau he thong",
        "minh se khong bat",
        "noi gon de de nho",
    ]
    return any(token in lower for token in filler_tokens)


def clean_history_title(title, fallback_index=1):
    title = re.sub(r"\s+", " ", str(title or "")).strip()
    if re.fullmatch(r"phần\s*\d+", title, flags=re.IGNORECASE):
        return title[:1].upper() + title[1:]
    for _ in range(4):
        before = title
        title = re.sub(r"^ý\s*[a-d]\s*[-:]\s*", "", title, flags=re.IGNORECASE)
        title = re.sub(r"^phần\s*\d+\s*[-:]\s*", "", title, flags=re.IGNORECASE)
        title = re.sub(r"^bước\s*\d+\s*[-:]\s*", "", title, flags=re.IGNORECASE)
        if title == before:
            break
    title = re.sub(r"\s*\(\d+/\d+\)\s*$", "", title).strip()
    if re.fullmatch(r"phần\s*\d+", title, flags=re.IGNORECASE):
        return title[:1].upper() + title[1:]
    if not title:
        return f"Phần {fallback_index}"
    return trim_display_line(title, 92)


def build_history_slide_text(step, max_lines=12, max_chars=680):
    slide_raw = narration_display_text(step.get("slide_text") or "")
    narration_raw = narration_display_text(step.get("narration") or "")
    use_slide = bool(
        slide_raw
        and "..." not in slide_raw
        and len(slide_raw.split()) >= 18
        and not is_history_filler_sentence(slide_raw)
    )

    lines = []
    if use_slide:
        for raw_line in slide_raw.replace("\r\n", "\n").replace("\r", "\n").splitlines():
            if is_history_filler_sentence(raw_line):
                continue
            for clean in wrap_display_text(raw_line, 58):
                if clean and "..." not in clean and not is_history_filler_sentence(clean):
                    lines.append(clean)

    slide_is_thin = len(" ".join(lines)) < 230 or len(lines) < 4
    if slide_is_thin:
        for sentence in sentence_candidates(narration_raw):
            if is_history_filler_sentence(sentence):
                sentence = re.sub(
                    r"^(Chào các em!|Các em có biết không,|Bây giờ chúng ta sang Phần \d+ nhé!|Ta bắt đầu hệ thống phần \d+:)\s*",
                    "",
                    sentence,
                    flags=re.IGNORECASE,
            ).strip()
            for clean in wrap_display_text(sentence, 58):
                if clean and "..." not in clean and clean not in lines:
                    lines.append(clean)
            if len(lines) >= max_lines or len(" ".join(lines)) >= max_chars:
                break

    compact = []
    total = 0
    for line in lines:
        if len(compact) >= max_lines:
            break
        if total + len(line) > max_chars and compact:
            break
        compact.append(line)
        total += len(line) + 1
    return "\n".join(compact) or clean_history_title(step.get("title"), 1)


def is_history_transition_step(step):
    title = str(step.get("title") or "").strip()
    body = str(step.get("slide_text") or step.get("narration") or "").strip()
    if not re.fullmatch(r"phần\s*\d+", title, flags=re.IGNORECASE):
        return False
    normalized = normalized_asset_text(body)
    return (
        normalized.startswith("ta bat dau he thong")
        or normalized.startswith("chu de lich su nay co cac y")
        or len(body.split()) < 35
    )


def restore_history_text(text):
    text = str(text or "")
    text = re.sub(r"\bchâu\s*φ\b", "châu Phi", text, flags=re.IGNORECASE)
    text = re.sub(r"\bchau\s*φ\b", "châu Phi", text, flags=re.IGNORECASE)
    text = re.sub(r"\bÁ,\s*φ\b", "Á, Phi", text)
    return text


def build_full_solution_text(steps):
    lines = []
    seen = set()
    item_index = 1
    for step in steps:
        if not isinstance(step, dict) or is_recap_step(step):
            continue
        title = re.sub(r"\s+", " ", str(step.get("title") or "")).strip()
        if re.fullmatch(r"Ý\s+[a-d]", title, flags=re.IGNORECASE):
            continue
        slide_text = scene_display_text(step)
        if len(re.findall(r"(?:^|\n)\s*[A-D][.)]\s", slide_text)) >= 4:
            # Question choices include distractors, not solution steps.
            continue
        formulas = formula_lines(step.get("latex") or "")
        title_label = title.replace("Ý a - ", "a) ").replace("Ý b - ", "b) ").replace("Ý c - ", "c) ").replace("Ý d - ", "d) ")
        if formulas:
            line = f"{item_index}. {title_label}" if title_label else f"{item_index}. Công thức"
            if line not in seen:
                lines.append(line)
                seen.add(line)
            for formula in formulas[:6]:
                clean_formula = compact_solution_line(formula, max_chars=150)
                formula_line = f"   {clean_formula}"
                if formula_line and formula_line not in seen:
                    lines.append(formula_line)
                    seen.add(formula_line)
            item_index += 1
            continue
        elif slide_text:
            body = slide_text.replace("\n", " ; ")
            line = f"{title_label}: {body}" if title_label else body
        else:
            continue
        line = re.sub(r"\s+", " ", line).strip()
        if not line or line in seen:
            continue
        seen.add(line)
        lines.append(f"{item_index}. {line}")
        item_index += 1
    return "\n".join(lines)


def ensure_full_solution_slide(script):
    steps = script.get("steps") if isinstance(script.get("steps"), list) else []
    if not steps:
        return script, False
    if any(
        "toàn bộ bài giải" in str(step.get("title") or "").lower()
        or "tóm tắt lời giải" in str(step.get("title") or "").lower()
        for step in steps
    ):
        return script, False
    full_text = build_full_solution_text(steps)
    if not full_text:
        return script, False
    steps.append({
        "title": "Tóm tắt lời giải",
        "narration": full_solution_chunk_speech(full_text),
        "slide_text": full_text,
        "latex": None,
        "geometry": None,
        "diagram": None,
        "visual": None,
        "layout": "full_solution",
    })
    script["steps"] = steps
    return script, True


def ask_gemini(problem, subject, image_path=None):
    selected_subject = re.sub(r"\s+", " ", str(subject or "").strip()) or "Toán học"
    subject = normalize_subject(selected_subject)
    subject_label = subject if selected_subject == subject else f"{subject} - {selected_subject}"
    api_keys = gemini_api_keys()
    has_image = bool(image_path and Path(image_path).exists())
    models = gemini_model_candidates()
    if has_image:
        image_model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.6-flash").strip()
        if image_model:
            models = [image_model] + [model for model in models if model != image_model]
    primary_model = models[0]
    if not api_keys:
        if allow_demo_fallback() and not has_image:
            return ensure_script_quality(demo_script(problem, subject), original_problem=problem, subject=subject)
        raise RuntimeError("Chưa cấu hình Gemini API key nên không thể đọc đề thật.")

    input_problem = str(problem or "").strip()
    ocr_problem = ""
    if has_image:
        ocr_problem = extract_problem_text_from_image(image_path, api_keys, gemini_image_model_candidates(), subject_label)
        if ocr_problem:
            problem = f"{input_problem}\n{ocr_problem}".strip() if input_problem else ocr_problem
        elif not input_problem:
            raise RuntimeError("Gemini OCR chưa đọc được nội dung trong ảnh đề bài.")
        rule_script = rule_based_script_from_problem(problem, subject)
        if rule_script:
            script = ensure_script_quality(rule_script, original_problem=problem, subject=subject)
            script["_ocr_problem"] = ocr_problem
            script["_model_used"] = "rule_based_geometry_after_ocr"
            return script

    subject_rules = ""
    if is_history_subject(subject):
        subject_rules = """
    Quy tac rieng cho Lich su:
    - Output bang tieng Viet tu nhien. Giong narration am ap, vui ve vua phai, co the dung vi du doi thuong de de nho.
    - Khong dua cau dua vao slide_text. Khong dua ve chien tranh, thuong vong, ton giao, dan toc hoac nhan vat lich su theo kieu cot dua.
    - slide_text la noi dung chinh nguoi xem can doc duoc tren slide, khong duoc qua ngan. Moi slide nen co 4-7 dong, moi dong 8-16 tu.
    - slide_text phai du y: moc thoi gian, boi canh, nguyen nhan, dien bien, ket qua, y nghia. Khong chi viet cau dem vui nhu "bay gio sang phan 2".
    - narration duoc giai thich them de voice doc, co the vui ve hon, nhung slide_text van phai du noi dung hoc tap.
    - Khong sinh cong thuc Toan/Ly cho Lich su. Tat ca truong latex cua step va final_latex phai la null.
    - Khong dung cac cum "bai toan", "cong thuc", "thay so", "dap so" trong noi dung Lich su.
    - Chia noi dung thanh Phan 1, Phan 2, Phan 3... trong title/slide_text, khong dung cach goi Y a/Y b tren slide.
    - Chon design_template/history_style phu hop trong: history_newspaper_1990, history_archive, history_timeline, history_strategy, history_biography, history_exam.
    - Moi step nen co visual neu co the. Visual dung mot trong cac type:
      timeline: {"type":"timeline","events":[{"date":"1945","label":"Su kien chinh"}]}
      cause_event_result: {"type":"cause_event_result","nodes":[{"label":"Nguyen nhan","text":"Y chinh"}]}
      compare_board: {"type":"compare_board","columns":[{"title":"Truoc","items":["..."]},{"title":"Sau","items":["..."]}]}
      character_card: {"type":"character_card","name":"Nhan vat","items":["Vai tro","Dong gop"]}
      document_card: {"type":"document_card","title":"Van kien/boi canh","items":["Y chinh"]}
      memory_summary: {"type":"memory_summary","title":"Can nho","items":["Tu khoa 1","Tu khoa 2"]}
    """
    elif is_physics_subject(subject):
        subject_rules = """
    Quy tắc riêng cho Vật lí:
    - Phải phân tích đúng đại lượng đã biết, đại lượng cần tìm và đơn vị SI.
    - Mỗi bước tính phải nêu rõ công thức vật lí, đổi đơn vị nếu có, thay số, rồi kết luận kèm đơn vị.
    - Không được chỉ biến bài Vật lí thành bài toán số học; phải giải thích ý nghĩa vật lí của công thức đang dùng.
    - Với cơ học, ưu tiên diagram.type = "force" hoặc "motion"; mô tả lực, vận tốc, gia tốc bằng mũi tên.
    - Với điện học, ưu tiên diagram.type = "circuit"; giữ các đại lượng U, I, R, P và đơn vị V, A, Ω, W.
    - Với quang học, ưu tiên diagram.type = "optics"; mô tả tia tới, tia phản xạ/tia ló, gương hoặc thấu kính.
    - Với sóng/dao động, ưu tiên diagram.type = "wave"; giữ chu kì T, tần số f, bước sóng λ, biên độ A.
    - Với nhiệt học, ưu tiên diagram.type = "heat"; giữ Q, m, c, Δt, nhiệt độ và đơn vị.
    - Mỗi step nên có diagram nếu có thể. Diagram chỉ dùng schema đơn giản: {"type":"force|motion|circuit|optics|wave|heat","labels":{"m":"m = 2 kg","F":"F = 10 N","U":"U = 12 V","I":"I = 2 A","R":"R = 6 Ω"}}.
    - Sơ đồ phải khớp đề, không bịa lực hoặc tự giả định cách mắc mạch. Nếu thiếu dữ kiện để vẽ, diagram = null.
    - Mạch điện: thêm topology = "single", "series" hoặc "parallel". series/parallel chỉ hỗ trợ đúng hai điện trở, thêm resistors = ["R₁ = ... Ω", "R₂ = ... Ω"]. Mạch hỗn hợp/phức tạp: diagram = null.
    - Lực/chuyển động: bắt buộc có vectors = [{"label":"F = ... N","direction":"right|left|up|down"}]. Chỉ vẽ vectơ đề cho hoặc đã suy ra có giải thích; tối đa một vectơ mỗi hướng. Không tự thêm N/P khi chưa có điều kiện mặt đỡ/trọng lực.
    - Quang học: chỉ vẽ thấu kính hội tụ với vật ngoài tiêu điểm, thêm focal_length và object_distance là số dương CÙNG ĐƠN VỊ; object_distance > focal_length. Các trường hợp khác: diagram = null.
    - wave là sóng hình sin theo vị trí x, không dùng cho đồ thị dao động theo thời gian hoặc con lắc. heat chỉ dùng khi mô tả hệ nhận nhiệt Q.
    - Bố cục: một ý chính mỗi bước. slide_text nên có 2-4 dòng ngắn (tổng dưới 320 ký tự khi có sơ đồ), công thức đặt riêng trong latex. Không nhắc lại một công thức cả ở slide_text lẫn latex.
    - Bước mở đầu giữ đầy đủ câu hỏi và lựa chọn nếu là trắc nghiệm. Bước kết luận ghi rõ đáp án, đơn vị và điều kiện áp dụng. Narration giải thích dài hơn phần chữ trên slide.
    """

    prompt = f"""Bạn là giáo viên giảng dạy môn {subject_label}. Hãy đọc đề bài bằng text và/hoặc ảnh, giải đúng và đủ như một video bài giảng.

    Quy tắc bắt buộc:
    - Nếu đề có các ý a), b), c), d), phải tách thành subproblems đủ từng ý, không bỏ sót.
    - Mỗi ý phải có ít nhất 2 bước giải và 1 final_answer rõ ràng.
    - Luôn có kết luận cho từng ý và summary tổng kết cuối bài.
    - Không trả lời quá ngắn. Không chỉ ghi đáp số.
    - Công thức để trong LaTeX hợp lệ, không bọc markdown.
    - Không dùng ký hiệu đô-la $...$ trong latex; chỉ ghi phần công thức.
    - Nếu có nhiều phép tính, dùng xuống dòng LaTeX bằng "\\\\" giữa các dòng.
    - Dùng lệnh LaTeX chuẩn như "\\vec{{AB}}", "\\begin{{cases}}...\\end{{cases}}", "\\sqrt{{...}}".
    - Tách rõ "narration" và "slide_text": narration là lời giáo viên giải thích đầy đủ để đọc voice; slide_text chỉ là chữ ngắn hiện trên slide.
    - slide_text không được chép nguyên narration. Chỉ ghi dữ kiện, công thức, thay số, kết luận chính; tối đa 3-5 dòng ngắn.
    - Nếu bước có latex, slide_text chỉ nên nêu nhãn như "Công thức và thay số:" hoặc một câu kết luận ngắn, không diễn giải dài.
    - Với bài hình học/tọa độ, mọi step liên quan hình phải có geometry.points đầy đủ các điểm đã biết để app vẽ hình bên phải.
    - Với bài đường tròn có đường kính AB và tiếp tuyến, có thể dùng geometry.type = "circle_diameter_tangent", diameter = ["A","B"], center = "O", points gồm A, B, O, C và các điểm D/E/F nếu có.
    - Narration là lời đọc tiếng Việt tự nhiên, đủ chi tiết cho video bài giảng.
    {subject_rules}

    Trả về JSON thuần, không markdown, theo schema:
    {{
      "problem": "Nội dung tóm tắt đề bài",
      "lesson_title": "Tiêu đề bài giảng",
      "design_template": "studio hoac history_newspaper_1990/history_archive/history_timeline/history_strategy/history_biography/history_exam",
      "history_style": "null neu khong phai Lich su, hoac mot history template id",
      "subproblems": [
        {{
          "label": "a",
          "question": "Nội dung ý a",
          "steps": [
            {{
              "title": "Tiêu đề bước",
              "narration": "Lời thuyết minh chi tiết",
              "slide_text": "Chữ ngắn hiện trên slide, chỉ gồm lời giải chính",
              "latex": "LaTeX hoặc null",
              "visual": {{ "type": "timeline", "events": [{{"date": "1945", "label": "Su kien chinh"}}] }} hoac null,
              "geometry": {{ "type": "coordinate", "points": {{"A": [1, 2], "B": [5, 4]}} }} hoặc {{ "type": "circle_diameter_tangent", "diameter": ["A", "B"], "center": "O", "points": {{"A": [-1, 0], "B": [1, 0], "O": [0, 0], "C": [0.38, 0.925]}} }} hoặc null,
              "diagram": {{ "type": "force", "labels": {{"m": "m = 2 kg", "F": "F = 10 N"}} }} hoặc null
            }}
          ],
          "final_answer": "Kết luận cuối ý này",
          "final_latex": "LaTeX kết luận hoặc null"
        }}
      ],
      "steps": [
        {{
          "title": "Dùng khi đề chỉ có một ý",
          "narration": "Lời thuyết minh",
          "slide_text": "Chữ ngắn hiện trên slide",
          "latex": "LaTeX hoặc null",
          "visual": null,
          "geometry": null,
          "diagram": null
        }}
      ],
      "summary": ["a) ...", "b) ..."]
    }}
    """

    text_prompt = prompt + f"\nĐề bài nhập từ user/OCR: {problem}" if problem else prompt

    request_timeout = env_int("GEMINI_REQUEST_TIMEOUT", 45, 15, 120)
    max_keys = env_int("GEMINI_MAX_KEYS", 3, 1, len(api_keys))
    solve_image_path = None if problem else image_path
    last_error = None
    attempted = 0
    for model in models:
        for api_key in api_keys[:max_keys]:
            attempted += 1
            try:
                script = ensure_script_quality(
                    gemini_generate_json(api_key, model, text_prompt, image_path=solve_image_path, timeout=request_timeout),
                    original_problem=problem,
                    subject=subject,
                )
                if has_image and is_default_demo_script(script):
                    raise RuntimeError("Gemini trả về kịch bản demo, không khớp ảnh đề bài.")
                if ocr_problem:
                    script["_ocr_problem"] = ocr_problem
                script["_model_used"] = model
                return script
            except Exception as e:
                last_error = e
                message = str(e).replace(api_key, "[MASKED_KEY]")
                print(f"Gemini API error with {model} {mask_secret(api_key)}: {message[:500]}")

    print(f"Gemini failed after {attempted} attempts across {len(models)} model(s). Last error: {last_error}")
    rule_script = rule_based_script_from_problem(problem, subject)
    if rule_script:
        script = ensure_script_quality(rule_script, original_problem=problem, subject=subject)
        if ocr_problem:
            script["_ocr_problem"] = ocr_problem
        script["_model_used"] = "rule_based_geometry_fallback"
        return script
    if allow_demo_fallback() and not has_image:
        return ensure_script_quality(demo_script(problem, subject), original_problem=problem, subject=subject)
    raise RuntimeError(
        f"Gemini không đọc/giải được đề bài sau {attempted} lượt thử. "
        "Vui lòng thử lại, nhập thêm phần text của đề, hoặc kiểm tra model/API key."
    )
























def coerce_points(raw_points):
    points = {}
    if not isinstance(raw_points, dict):
        return points
    for name, value in raw_points.items():
        if not isinstance(value, (list, tuple)) or len(value) < 2:
            continue
        try:
            points[str(name)] = (float(value[0]), float(value[1]))
        except (TypeError, ValueError):
            continue
    return points


def extract_points_from_text(text):
    points = {}
    pattern = re.compile(
        r"\b([A-Z])\s*\(\s*(-?\d+(?:[.,]\d+)?)\s*[;,]\s*(-?\d+(?:[.,]\d+)?)\s*\)"
    )
    for name, raw_x, raw_y in pattern.findall(str(text or "")):
        try:
            x = float(raw_x.replace(",", "."))
            y = float(raw_y.replace(",", "."))
            points[name] = [x, y]
        except ValueError:
            continue
    return points


def enrich_geometry_from_problem(script):
    problem = f"{script.get('problem') or ''} {script.get('_input_problem') or ''}"
    points = extract_points_from_text(problem)
    circle_geometry = infer_circle_geometry_from_text(problem)
    if circle_geometry:
        script["detected_geometry"] = circle_geometry
        for step in script.get("steps") or []:
            if step.get("geometry"):
                continue
            step["geometry"] = circle_geometry
        return script

    if not points:
        return script
    detected_geometry = {"points": points, "type": "coordinate"}
    script["detected_geometry"] = detected_geometry
    for step in script.get("steps") or []:
        if step.get("geometry"):
            continue
        step["geometry"] = detected_geometry
    return script


PHYSICS_DIAGRAM_TYPES = {"force", "motion", "circuit", "optics", "wave", "heat"}


def normalized_search_text(value):
    raw = str(value or "")
    normalized = unicodedata.normalize("NFD", raw)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.lower()


def strip_physics_diagrams(script):
    if not isinstance(script, dict):
        return script
    detected = script.get("detected_diagram")
    if isinstance(detected, dict) and str(detected.get("type") or "").lower() in PHYSICS_DIAGRAM_TYPES:
        script.pop("detected_diagram", None)
    for step in script.get("steps") or []:
        diagram = step.get("diagram") if isinstance(step, dict) else None
        if isinstance(diagram, dict) and str(diagram.get("type") or "").lower() in PHYSICS_DIAGRAM_TYPES:
            step["diagram"] = None
    return script


def looks_like_physics_problem(text, subject=None):
    if not is_physics_subject(subject):
        return False
    text = normalized_search_text(text)
    physics_tokens = [
        "vat li", "vat ly", "luc", "van toc", "gia toc", "khoi luong", "trong luong", "ma sat",
        "dien", "dong dien", "hieu dien the", "dien tro", "cong suat", "mach",
        "quang", "guong", "thau kinh", "tia sang", "song", "dao dong", "nhiet",
        "nhiet luong", "ap suat", "newton", "jun", "ampe", "von", "ohm",
    ]
    unit_patterns = [
        r"\b\d+(?:[.,]\d+)?\s*(?:kg|n|j|w|a|v|hz|ohm)\b",
        r"\b\d+(?:[.,]\d+)?\s*m/s(?:\^?2|2)?\b",
        r"\b[ufirp]\s*=\s*-?\d",
        r"\b[av]\s*=\s*-?\d+(?:[.,]\d+)?\s*m/s",
    ]
    return any(token in text for token in physics_tokens) or any(
        re.search(pattern, text, flags=re.IGNORECASE) for pattern in unit_patterns
    )


def infer_physics_diagram_from_text(text, subject=None):
    if not looks_like_physics_problem(text, subject):
        return None
    source = str(text or "")
    lower = source.lower()
    labels = {}

    def capture(label, pattern, unit):
        match = re.search(pattern, source)
        # Do not silently relabel grams as kilograms or milliamps as amps.
        units = {'kg': r'kg$', 'N': r'N$', 'm/s^2': r'm/s(?:\^?2|²)$',
                 'm/s': r'm/s$', 'V': r'V$', 'A': r'A$', 'Ω': r'(?:Ω|ohm|ôm)$'}
        if match and re.search(units[unit], match.group(0)):
            labels[label] = f"{label} = {match.group(1).replace(',', '.')} {unit}".strip()

    capture("m", r"\bm\s*=\s*(-?\d+(?:[.,]\d+)?)\s*(?:kg|ki\s*lô\s*gam)?", "kg")
    capture("F", r"\bF\s*=\s*(-?\d+(?:[.,]\d+)?)\s*(?:N|niutơn|newton)?", "N")
    capture("a", r"\ba\s*=\s*(-?\d+(?:[.,]\d+)?)\s*(?:m/s\^?2|m/s²)?", "m/s^2")
    capture("v", r"\bv\s*=\s*(-?\d+(?:[.,]\d+)?)\s*(?:m/s)?", "m/s")
    capture("U", r"\bU\s*=\s*(-?\d+(?:[.,]\d+)?)\s*(?:V|vôn)?", "V")
    capture("I", r"\bI\s*=\s*(-?\d+(?:[.,]\d+)?)\s*(?:A|ampe)?", "A")
    capture("R", r"\bR\s*=\s*(-?\d+(?:[.,]\d+)?)\s*(?:Ω|ohm|ôm)?", "Ω")

    if any(token in lower for token in ["mạch", "mach", "điện", "dien", "dòng điện", "dong dien", "hiệu điện thế", "hieu dien the", "điện trở", "dien tro", "ampe", "vôn", "von", "ôm", "ohm"]):
        if any(word in lower for word in ['song song', 'nối tiếp', 'hỗn hợp', 'tụ điện', 'cuộn cảm', 'điện trường']):
            return None  # Topology must come from an explicit validated diagram.
        if re.search(r'(?:hai|ba|bốn|2|3|4)\s+điện trở|R[₁₂12]', source, re.IGNORECASE):
            return None
        return {"type": "circuit", "topology": "single", "labels": labels} if 'R' in labels else None
    if any(token in lower for token in ["gương", "guong", "thấu kính", "thau kinh", "tia sáng", "tia sang", "quang", "tiêu cự", "tieu cu", "ảnh ảo", "anh ao", "ảnh thật", "anh that"]):
        return {"type": "optics", "labels": labels}
    if any(token in lower for token in ["bước sóng", "sóng hình sin", "sóng cơ", "sóng điện từ"]):
        return {"type": "wave", "labels": labels}
    if any(token in lower for token in ["nhiệt", "nhiet", "nhiệt lượng", "nhiet luong", "truyền nhiệt", "truyen nhiet", "nhiệt dung", "nhiet dung", "nhiệt độ", "nhiet do"]):
        return {"type": "heat", "labels": labels} if 'nhận nhiệt' in lower else None
    if any(token in lower for token in ["rơi", "roi", "ném", "nem", "chuyển động", "chuyen dong", "vận tốc", "van toc", "gia tốc", "gia toc"]):
        return {"type": "motion", "labels": labels}
    if any(token in lower for token in ["trọng lực", "ma sát", "hợp lực", "lực kéo", "lực đẩy"]) or "F" in labels:
        return {"type": "force", "labels": labels}
    return None


def enrich_physics_from_problem(script, subject=None):
    subject = normalize_subject(subject or script.get("subject"))
    if not is_physics_subject(subject):
        return strip_physics_diagrams(script)
    problem = f"{script.get('problem') or ''} {script.get('_input_problem') or ''}"
    if not looks_like_physics_problem(problem, subject):
        return script
    script["subject"] = "Vật lý"
    detected_diagram = infer_physics_diagram_from_text(problem, subject)
    if not detected_diagram:
        return script
    script["detected_diagram"] = detected_diagram
    detected_labels = detected_diagram.get("labels") if isinstance(detected_diagram.get("labels"), dict) else {}
    for step in script.get("steps") or []:
        if step.get("diagram"):
            step_labels = step["diagram"].get("labels") if isinstance(step["diagram"].get("labels"), dict) else {}
            step["diagram"]["labels"] = {**detected_labels, **step_labels}
            continue
        step_text = f"{step.get('title') or ''} {step.get('narration') or ''} {step.get('latex') or ''}"
        step_diagram = infer_physics_diagram_from_text(step_text, subject) or dict(detected_diagram)
        step_labels = step_diagram.get("labels") if isinstance(step_diagram.get("labels"), dict) else {}
        step_diagram["labels"] = {**detected_labels, **step_labels}
        step["diagram"] = step_diagram
    return script


def history_visual_text_blob(step):
    raw = " ".join(
        str(step.get(key) or "")
        for key in ("title", "slide_text", "narration")
    )
    normalized = unicodedata.normalize("NFD", raw)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.lower()


def infer_history_visual_from_text(step, step_index=0):
    text = history_visual_text_blob(step)
    title = str(step.get("title") or "").strip() or f"Step {step_index + 1}"
    slide_text = scene_display_text(step) if "scene_display_text" in globals() else str(step.get("slide_text") or step.get("narration") or "")
    lines = [line.strip(" -•\t") for line in str(slide_text).splitlines() if line.strip()]
    if not lines:
        lines = [title]

    if any(token in text for token in ["timeline", "moc thoi gian", "dien bien", "giai doan", "nam ", "the ky"]):
        events = []
        for line in lines[:5]:
            date_match = re.search(r"(\d{3,4}|trước|sau|đầu|giữa|cuối)", line, re.IGNORECASE)
            date = date_match.group(1) if date_match else f"Mốc {len(events) + 1}"
            events.append({"date": date, "label": re.sub(r"^\d{3,4}\s*[:.-]?\s*", "", line).strip() or line})
        return {"type": "timeline", "events": events}

    if any(token in text for token in ["nguyen nhan", "vi sao", "ket qua", "y nghia", "tac dong", "he qua", "cause"]):
        nodes = []
        labels = ["Nguyên nhân", "Diễn biến", "Kết quả", "Ý nghĩa"]
        for idx, line in enumerate(lines[:4]):
            nodes.append({"label": labels[idx] if idx < len(labels) else f"Ý {idx + 1}", "text": line})
        return {"type": "cause_event_result", "nodes": nodes}

    if any(token in text for token in ["so sanh", "giong", "khac", "truoc", "sau", "doi lap", "compare"]):
        midpoint = max(1, len(lines) // 2)
        return {
            "type": "compare_board",
            "columns": [
                {"title": "Nhóm 1", "items": lines[:midpoint][:4]},
                {"title": "Nhóm 2", "items": lines[midpoint:][:4] or lines[:midpoint][:4]},
            ],
        }

    if any(token in text for token in ["nhan vat", "lanh dao", "vua", "chu tich", "tuong", "person", "biography"]):
        return {"type": "character_card", "name": title, "items": lines[:4]}

    if any(token in text for token in ["van kien", "hiep uoc", "tuyen ngon", "chinh sach", "boi canh", "ho so", "document"]):
        return {"type": "document_card", "title": title, "items": lines[:5]}

    return {"type": "memory_summary", "title": title, "items": lines[:6]}


def enrich_history_from_problem(script, subject=None):
    subject = normalize_subject(subject or script.get("subject"))
    if not is_history_subject(subject):
        return script
    script["subject"] = "Lịch sử"
    script.setdefault("design_template", script.get("history_style") or "history_newspaper_1990")
    script.setdefault("history_style", script.get("design_template") or "history_newspaper_1990")
    for index, step in enumerate(script.get("steps") or []):
        if isinstance(step.get("visual"), dict) and step.get("visual", {}).get("type"):
            continue
        step["visual"] = infer_history_visual_from_text(step, index)
    return script


def normalized_asset_text(value):
    raw = unicodedata.normalize("NFD", str(value or ""))
    without_marks = "".join(ch for ch in raw if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^0-9a-zA-Z]+", " ", without_marks).lower().strip()


def history_asset_score(step, asset):
    text = normalized_asset_text(
        " ".join(str(step.get(key) or "") for key in ("title", "slide_text", "narration", "section_label"))
    )
    caption = normalized_asset_text(
        " ".join(str(asset.get(key) or "") for key in ("caption", "original_name", "filename", "id"))
    )
    if not text or not caption:
        return 0
    caption_terms = [term for term in caption.split() if len(term) >= 3]
    return sum(1 for term in caption_terms if term in text)


def apply_history_assets(script, assets):
    if not isinstance(script, dict) or not assets:
        return script
    if not is_history_subject(script.get("subject")):
        return script

    clean_assets = []
    for index, asset in enumerate(assets[:4], start=1):
        if not isinstance(asset, dict) or not asset.get("path"):
            continue
        clean_assets.append({
            "id": str(asset.get("id") or f"anh{index}"),
            "filename": str(asset.get("filename") or Path(str(asset.get("path"))).name),
            "original_name": str(asset.get("original_name") or asset.get("filename") or ""),
            "path": str(asset.get("path")),
            "url": str(asset.get("url") or ""),
            "caption": str(asset.get("caption") or asset.get("original_name") or f"Ảnh minh họa {index}").strip(),
        })
    if not clean_assets:
        return script

    script["history_assets"] = clean_assets
    steps = [step for step in (script.get("steps") or []) if isinstance(step, dict)]
    max_scores = {
        asset["path"]: max((history_asset_score(step, asset) for step in steps), default=0)
        for asset in clean_assets
    }
    usage = {asset["path"]: 0 for asset in clean_assets}

    for index, step in enumerate(script.get("steps") or []):
        if not isinstance(step, dict):
            continue

        unused = [asset for asset in clean_assets if usage.get(asset["path"], 0) == 0]
        if unused:
            selected = max(
                unused,
                key=lambda asset: (history_asset_score(step, asset), -clean_assets.index(asset)),
            )
        else:
            scores = {asset["path"]: history_asset_score(step, asset) for asset in clean_assets}
            best_score = max(scores.values(), default=0)
            min_usage = min(usage.values(), default=0)
            candidates = [asset for asset in clean_assets if usage.get(asset["path"], 0) <= min_usage]
            if best_score >= 2:
                strong = [
                    asset for asset in clean_assets
                    if scores.get(asset["path"], 0) == best_score and usage.get(asset["path"], 0) <= min_usage + 1
                ]
                candidates = strong or candidates
            selected = max(
                candidates,
                key=lambda asset: (scores.get(asset["path"], 0), -usage.get(asset["path"], 0), -clean_assets.index(asset)),
            )

        step["image_ref"] = selected["path"]
        step["image_caption"] = selected["caption"]

        usage[selected["path"]] = usage.get(selected["path"], 0) + 1

    warnings = []
    for asset in clean_assets:
        if max_scores.get(asset["path"], 0) <= 0:
            warnings.append(f"Ảnh '{asset['caption']}' chưa khớp rõ với nội dung; hệ thống sẽ dùng luân phiên nếu bạn vẫn render.")
        if usage.get(asset["path"], 0) <= 0:
            warnings.append(f"Ảnh '{asset['caption']}' chưa được gắn vào scene nào vì số cảnh quá ít.")
    if warnings:
        quality = script.get("quality") if isinstance(script.get("quality"), dict) else {}
        existing = quality.get("warnings") if isinstance(quality.get("warnings"), list) else []
        quality["warnings"] = list(dict.fromkeys(existing + warnings))[:20]
        script["quality"] = quality
    return script


def physics_diagram_svg_markup(diagram):
    return physics_svg(diagram, get_design_template('studio'))


def visual_items(visual, keys=("items", "nodes", "events")):
    for key in keys:
        value = visual.get(key)
        if isinstance(value, list) and value:
            return value
    return []


def item_label(item, *keys, fallback=""):
    if isinstance(item, dict):
        for key in keys:
            value = item.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
    return str(item or fallback).strip()


def history_visual_row(item, index=0):
    if isinstance(item, dict):
        date = item_label(item, "date", "year", "time", fallback="")
        heading = item_label(item, "label", "title", fallback="")
        body = item_label(item, "text", "description", "value", fallback="")
        if date:
            return date, heading or body or f"Mốc {index + 1}"
        if heading and body and heading != body:
            return heading, body
        return f"{index + 1}", heading or body or f"Ý chính {index + 1}"
    return f"{index + 1}", str(item or f"Ý chính {index + 1}").strip()


def compact_history_visual_text(text, max_chars=84):
    text = restore_history_text(re.sub(r"\s+", " ", str(text or "")).strip(" -•\t"))
    text = re.sub(r"^(?:[a-dA-D]\))\s*[:.\-]?\s*", "", text)
    text = re.sub(r"\s*(?:\.\.\.|…)\s*$", "", text).strip()
    if len(text) <= max_chars:
        return text
    for delimiter in ("; ", ". ", ", "):
        first = text.split(delimiter, 1)[0].strip()
        if 24 <= len(first) <= max_chars:
            return first
    return trim_display_line(text, max_chars)


def history_summary_rows_from_scene(scene):
    if not isinstance(scene, dict):
        return []
    title_text = f"{scene.get('title') or ''} {scene.get('slide_text') or ''} {scene.get('narration') or ''}"
    if not any(token in normalized_asset_text(title_text) for token in ("tong ket", "tom tat", "ket luan")):
        return []
    text = restore_history_text(scene_display_text(scene))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^Tổng\s*kết\s*:\s*", "", text, flags=re.I)
    matches = re.findall(r"(?:^|\s)([a-dA-D]\))\s*(.*?)(?=\s+[a-dA-D]\)|$)", text)
    rows = []
    for _, body in matches[:3]:
        body = compact_history_visual_text(body, 120)
        if not body:
            continue
        if "," in body:
            label, detail = body.split(",", 1)
            rows.append((compact_history_visual_text(label, 24), compact_history_visual_text(detail, 82)))
        else:
            rows.append((f"Ý {len(rows) + 1}", body))
    if rows:
        return rows
    lines = [compact_history_visual_text(line, 92) for line in text.split(". ") if line.strip()]
    return [(f"Ý {index + 1}", line) for index, line in enumerate(lines[:3]) if line]


def history_visual_rows(visual, scene=None):
    summary_rows = history_summary_rows_from_scene(scene)
    if summary_rows:
        return summary_rows, True

    rows = []
    if str((visual or {}).get("type") or "").lower() == "compare_board":
        columns = visual.get("columns") if isinstance(visual.get("columns"), list) else []
        for col in columns[:2]:
            title = item_label(col, "title", "label", fallback="Nhóm")
            items = col.get("items") if isinstance(col, dict) and isinstance(col.get("items"), list) else []
            rows.append((title, "; ".join(str(item) for item in items[:2])))
    else:
        for index, item in enumerate(visual_items(visual or {}, ("events", "nodes", "items"))[:4]):
            rows.append(history_visual_row(item, index))
    return rows, False


def history_visual_svg_markup(visual, theme, scene=None):
    visual = visual or {}
    primary = theme["primary"]
    accent = theme["accent"]
    accent_light = theme["accent_light"]
    text = theme["text"]
    card = theme["card"]
    border = theme["border"]

    rows, scene_is_summary = history_visual_rows(visual, scene)
    if not rows:
        rows = [("1", "Bối cảnh"), ("2", "Diễn biến"), ("3", "Kết quả"), ("4", "Ý nghĩa")]

    title_text = str(visual.get("title") or "Sơ đồ ghi nhớ")
    is_summary = scene_is_summary or any(token in normalized_asset_text(title_text) for token in ("tong ket", "tom tat", "ket luan"))
    max_rows = 3 if is_summary else 4
    title = escape(trim_display_line(title_text, 34))
    blocks = []
    for index, (label, body) in enumerate(rows[:max_rows]):
        y = 70 + index * 58
        label = escape(compact_history_visual_text(label or f"{index + 1}", 22))
        body = escape(compact_history_visual_text(body, 92 if not is_summary else 78))
        blocks.append(f'''
          <g>
            <rect x="30" y="{y}" width="500" height="50" rx="11" fill="{accent_light}" stroke="{border}" stroke-width="2"/>
            <circle cx="60" cy="{y + 25}" r="16" fill="{accent}"/>
            <text x="60" y="{y + 31}" text-anchor="middle" font-size="16" font-weight="900" fill="#FFFFFF">{index + 1}</text>
            <foreignObject x="90" y="{y + 7}" width="418" height="38">
              <div xmlns="http://www.w3.org/1999/xhtml" style="font:850 16px/1.2 Arial;color:{text};overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical">
                <span style="color:{accent};font-weight:900">{label}</span> {body}
              </div>
            </foreignObject>
          </g>
        ''')
    return f'''
    <svg class="history-svg" viewBox="0 0 560 320" role="img" aria-label="Tóm tắt ghi nhớ">
      <rect x="16" y="16" width="528" height="288" rx="18" fill="{card}" stroke="{border}" stroke-width="3"/>
      <text x="36" y="50" font-size="24" font-weight="900" fill="{primary}">{title}</text>
      {"".join(blocks)}
    </svg>'''


def scene_visual_markup(scene, theme=None):
    theme = theme or get_design_template("studio")
    if isinstance(scene.get("visual"), dict):
        return history_visual_svg_markup(scene.get("visual"), theme, scene)
    if isinstance(scene.get("diagram"), dict):
        return physics_svg(scene.get("diagram"), theme)
    return geometry_svg_markup(scene.get("geometry") or {})


def geometry_svg_markup(geometry):
    points = coerce_points((geometry or {}).get("points", {}))
    if not points:
        return '<div class="empty-visual">Lesson Loom</div>'

    if (geometry or {}).get("type") == "circle_diameter_tangent":
        xs = [point[0] for point in points.values()] + [-1.2, 1.2]
        ys = [point[1] for point in points.values()] + [-1.2, 1.2]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max(max_x - min_x, 1)
        height = max(max_y - min_y, 1)
        pad = max(width, height) * 0.12
        view_box = f"{min_x - pad:.3f} {-max_y - pad:.3f} {width + pad * 2:.3f} {height + pad * 2:.3f}"
        diameter = (geometry or {}).get("diameter") or ["A", "B"]
        center = (geometry or {}).get("center") or "O"

        def p(name):
            x, y = points[name]
            return x, -y

        def svg_line(a, b, color="#2B4C7E", width_value=0.035):
            if a not in points or b not in points:
                return ""
            x1, y1 = p(a)
            x2, y2 = p(b)
            stroke = max(width, height) * width_value
            return f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{stroke:.3f}" stroke-linecap="round"/>'

        markup = [f'<circle cx="{points.get(center, [0, 0])[0]:.3f}" cy="{-points.get(center, [0, 0])[1]:.3f}" r="1" fill="none" stroke="#2B4C7E" stroke-width="{max(width, height) * 0.03:.3f}"/>']
        for a, b in [(diameter[0], diameter[1]), (diameter[0], "C"), (diameter[1], "C"), ("C", "D"), (diameter[0], "E"), (diameter[1], "F")]:
            markup.append(svg_line(a, b))
        for a, b in [(diameter[0], "F"), (diameter[1], "E")]:
            markup.append(svg_line(a, b, color="#3AAFA9", width_value=0.02))
        dot_radius = max(width, height) * 0.035
        label_offset = max(width, height) * 0.07
        for name, (x, y) in points.items():
            markup.append(
                f'<circle cx="{x:.3f}" cy="{-y:.3f}" r="{dot_radius:.3f}" fill="#3AAFA9" stroke="#2B4C7E" stroke-width="{dot_radius * 0.25:.3f}"/>'
                f'<text x="{x + label_offset:.3f}" y="{-y - label_offset:.3f}" font-size="{max(width, height) * 0.11:.3f}" font-weight="700" fill="#1F2937">{escape(name)}</text>'
            )
        return f'<svg class="geometry-svg" viewBox="{view_box}" role="img" aria-label="Hình đường tròn">{"".join(markup)}</svg>'

    xs = [point[0] for point in points.values()]
    ys = [point[1] for point in points.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max(max_x - min_x, 1)
    height = max(max_y - min_y, 1)
    pad = max(width, height) * 0.22
    view_box = f"{min_x - pad:.3f} {-max_y - pad:.3f} {width + pad * 2:.3f} {height + pad * 2:.3f}"

    transformed = [(name, x, -y) for name, (x, y) in points.items()]
    polyline = ""
    if len(transformed) >= 2:
        coords = " ".join(f"{x:.3f},{y:.3f}" for _, x, y in transformed)
        if len(transformed) >= 3:
            coords = f"{coords} {transformed[0][1]:.3f},{transformed[0][2]:.3f}"
        polyline = f'<polyline points="{coords}" fill="none" stroke="#2B4C7E" stroke-width="{max(width, height) * 0.035:.3f}" stroke-linejoin="round" stroke-linecap="round"/>'

    dot_radius = max(width, height) * 0.055
    label_offset = max(width, height) * 0.12
    labels = []
    for name, x, y in transformed:
        labels.append(
            f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{dot_radius:.3f}" fill="#3AAFA9" stroke="#2B4C7E" stroke-width="{dot_radius * 0.25:.3f}"/>'
            f'<text x="{x + label_offset:.3f}" y="{y - label_offset:.3f}" font-size="{max(width, height) * 0.16:.3f}" font-weight="700" fill="#1F2937">{escape(name)}</text>'
        )

    return (
        f'<svg class="geometry-svg" viewBox="{view_box}" role="img" aria-label="Hình minh hoạ">'
        f"{polyline}{''.join(labels)}</svg>"
    )


def latex_to_text(value):
    text = str(value or "").strip()
    if not text:
        return ""

    text = text.replace("$$", "$").strip("$")
    text = re.sub(r"\\\\(?=[A-Za-z])", lambda _match: "\\", text)
    text = text.replace("\\\\", "\n")
    text = re.sub(r"\$([^$]+)\$", r"\1", text)
    text = re.sub(r"\bvec\s*([A-Z]{2})\b", r"\\vec{\1}", text)
    text = re.sub(r"\bvec([A-Z]{2})\b", r"\\vec{\1}", text)
    text = text.replace("begincases", "\\begin{cases}").replace("endcases", "\\end{cases}")
    text = text.replace("\\_", "_")
    replacements = {
        "\\quad": " ",
        "\\qquad": " ",
        "\\,": " ",
        "\\;": " ",
        "\\:": " ",
        "\\times": "×",
        "\\cdot": "·",
        "\\cos": "cos",
        "\\sin": "sin",
        "\\tan": "tan",
        "\\omega": "ω",
        "\\Omega": "Ω",
        "\\varphi": "φ",
        "\\phi": "φ",
        "\\pi": "π",
        "\\lambda": "λ",
        "\\perp": " vuông góc ",
        "\\parallel": " // ",
        "\\Delta": "tam giác ",
        "\\triangle": "tam giác ",
        "\\left": "",
        "\\right": "",
        "\\le": "≤",
        "\\ge": "≥",
        "\\neq": "≠",
        "\\approx": "≈",
        "\\pm": "±",
        "\\Rightarrow": "⇒",
        "\\rightarrow": "→",
        "\\circ": "°",
        "\\begin{cases}": "",
        "\\end{cases}": "",
        "\\begin{aligned}": "",
        "\\end{aligned}": "",
        "\\begin{array}": "",
        "\\end{array}": "",
        "\\text": "",
        "\\mathrm": "",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    text = re.sub(r"\\(?:dfrac|frac)\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"(\1)/(\2)", text)
    text = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"√(\1)", text)
    text = re.sub(r"\\widehat\s*\{([^{}]+)\}", r"góc \1", text)
    text = re.sub(r"\\angle\s*\{?([A-Za-z0-9]+)\}?", r"góc \1", text)
    text = re.sub(r"\\vec\s*\{([^{}]+)\}", r"→\1", text)
    text = re.sub(r"(→[A-Za-z0-9]+)\s*·\s*(→[A-Za-z0-9]+)", r"\1 · \2", text)
    text = text.replace("^°", "°")
    text = re.sub(r"\^\s*\{?2\}?", "²", text)
    text = re.sub(r"\^\s*\{?3\}?", "³", text)
    text = re.sub(r"\^\s*\{([^{}]+)\}", r"^\1", text)
    text = re.sub(r"_\s*\{([^{}]+)\}", r"_\1", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\(([^()\s]+)\)/\(([^()\s]+)\)", r"\1/\2", text)
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)
    lines = []
    for line in text.splitlines():
        clean = re.sub(r"\s+", " ", line).strip()
        if clean:
            lines.append(clean)
    return "\n".join(lines) if lines else re.sub(r"\s+", " ", text).strip()


def narration_display_text(value):
    text = latex_to_text(value)
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    symbol_words = {
        r"\bomega\b": "ω",
        r"\bvarphi\b": "φ",
        r"(?<![A-Za-z])pi\b": "π",
        r"\blambda\b": "λ",
    }
    for pattern, replacement in symbol_words.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\s*;\s*(?=[a-d]\))", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!^)(?<!\n)\s+(?=[a-d]\))", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"(Tổng kết(?: lời giải)?:)\s*", r"\1\n", text, flags=re.IGNORECASE)
    lines = []
    for line in text.splitlines():
        clean = re.sub(r"\s+", " ", line).strip()
        if clean:
            lines.append(clean)
    labeled_lines = [
        line for line in lines
        if re.match(r"([a-d])\s*[\).]", line, re.IGNORECASE)
    ]
    if len(labeled_lines) >= 2:
        filtered = []
        seen_labels = set()
        for line in lines:
            label_match = re.match(r"([a-d])\s*[\).]", line, re.IGNORECASE)
            if label_match:
                label = label_match.group(1).lower()
                if label in seen_labels:
                    continue
                seen_labels.add(label)
            filtered.append(line)
        lines = filtered
    return "\n".join(lines)


def cleanup_symbol_words(text):
    text = str(text or "")
    symbol_words = {
        r"\bomega\b": "ω",
        r"\bvarphi\b": "φ",
        r"(?<![A-Za-z])pi\b": "π",
        r"\blambda\b": "λ",
    }
    for pattern, replacement in symbol_words.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def sentence_candidates(text):
    clean = narration_display_text(text)
    pieces = []
    for line in clean.splitlines():
        parts = re.split(r"(?<=[.!?])\s+", line)
        pieces.extend(part.strip(" -") for part in parts if part.strip(" -"))
    return pieces


def concise_sentence_for_slide(text, max_chars=150):
    priority_tokens = [
        "dữ kiện", "đã biết", "cần tìm", "ta có", "suy ra", "vậy", "kết luận",
        "thay", "đổi đơn vị", "áp dụng", "công thức",
    ]
    sentences = sentence_candidates(text)
    if not sentences:
        return ""
    selected = []
    for sentence in sentences:
        lower = sentence.lower()
        if any(token in lower for token in priority_tokens):
            selected.append(sentence)
        if len(" ".join(selected)) >= max_chars:
            break
    if not selected:
        selected = sentences[:1]
    result = " ".join(selected)
    result = re.sub(r"^(chào các em[!,.\s]*)", "", result, flags=re.IGNORECASE).strip()
    result = cleanup_symbol_words(result)
    if len(result) <= max_chars:
        return result
    return result[:max_chars].rsplit(" ", 1)[0].strip() + "..."


def build_slide_text(step):
    existing = narration_display_text(step.get("slide_text") or "")
    # Explicitly authored slide text may contain all four answer choices.
    # Replacing it with a narration summary silently loses the question.
    if existing:
        return existing

    title = str(step.get("title") or "")
    narration = step.get("narration") or ""
    latex = step.get("latex") or ""
    formulas = formula_lines(latex)
    lower_title = title.lower()

    if formulas and "kết luận" not in lower_title and "tổng kết" not in lower_title:
        if any(token in lower_title for token in ["dữ kiện", "tóm tắt"]):
            return "Dữ kiện:"
        if any(token in lower_title for token in ["thay", "tính", "áp dụng"]):
            return "Công thức và thay số:"
        return "So sánh và rút ra đại lượng:"

    if existing and len(existing) <= 120:
        return existing

    if "tổng quan" in lower_title:
        lines = []
        for line in narration_display_text(narration).splitlines():
            if re.match(r"[a-d]\s*[\).]", line, re.IGNORECASE):
                lines.append(line)
        return "\n".join(lines[:5]) or concise_sentence_for_slide(narration, 160)

    if "kết luận" in lower_title or "tổng kết" in lower_title:
        clean = narration_display_text(narration)
        if clean.lower().startswith("tổng kết:"):
            return clean
        summary = concise_sentence_for_slide(narration, 180)
        if formulas:
            return "\n".join([summary] + formulas[:3]) if summary else "\n".join(formulas[:4])
        return summary

    if formulas:
        lead = concise_sentence_for_slide(narration, 120)
        if lead:
            return lead
        return "Công thức và thay số:"

    return concise_sentence_for_slide(narration, 170)


def scene_display_text(scene):
    if str(scene.get("layout") or "") == "full_solution":
        raw = scene.get("slide_text") or scene.get("narration") or ""
        text = cleanup_symbol_words(latex_to_text(raw))
        lines = []
        for line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
            clean = re.sub(r"\s+", " ", line).strip()
            if clean:
                lines.append(clean)
        return "\n".join(lines)
    return narration_display_text(scene.get("slide_text") or build_slide_text(scene))


def full_solution_items(scene):
    raw = scene.get("slide_text") or scene.get("narration") or ""
    text = cleanup_symbol_words(latex_to_text(raw))
    items = []
    current = None
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        match = re.match(r"^(\d+)\.\s*(.*)$", line)
        if match:
            if current:
                items.append(current)
            current = {"index": match.group(1), "title": match.group(2).strip() or "Bước giải", "lines": []}
            continue
        if current is None:
            current = {"index": str(len(items) + 1), "title": "Kết quả chính", "lines": []}
        current["lines"].append(line)
    if current:
        items.append(current)
    return items


def full_solution_markup(scene):
    items = full_solution_items(scene)
    if not items:
        return escape(scene_display_text(scene))

    cards = []
    for item in items:
        line_markup = []
        for line in item["lines"]:
            lower = line.lower()
            classes = ["solution-line"]
            if any(symbol in line for symbol in ["=", "⇒", "≤", "≥", "λ", "ω", "φ", "π"]):
                classes.append("formula-line")
            if "kết luận" in lower or "vậy" in lower:
                classes.append("result-line")
            line_markup.append(f'<div class="{" ".join(classes)}">{escape(line)}</div>')
        cards.append(
            '<article class="solution-card">'
            f'<div class="solution-index">{escape(item["index"]).zfill(2)}</div>'
            '<div class="solution-body">'
            f'<h2>{escape(item["title"])}</h2>'
            f'<div class="solution-lines">{"".join(line_markup)}</div>'
            '</div>'
            '</article>'
        )
    return f'<div class="solution-grid">{"".join(cards)}</div>'


def expression_speech_text(value):
    text = str(value or "")
    replacements = {
        "\\frac": " phân số ",
        "\\sqrt": " căn ",
        "\\in": " thuộc ",
        "∈": " thuộc ",
        "⇒": " suy ra ",
        "=>": " suy ra ",
        "≤": " nhỏ hơn hoặc bằng ",
        "≥": " lớn hơn hoặc bằng ",
        "≠": " khác ",
        "≈": " xấp xỉ ",
        "⊥": " vuông góc ",
        "²": " bình phương ",
        "³": " lập phương ",
        "^2": " bình phương ",
        "^3": " lập phương ",
        "+": " cộng ",
        "=": " bằng ",
        "/": " trên ",
        ";": ", ",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"(?<!\w)-(?=\d)", " âm ", text)
    text = re.sub(r"(?<=[\w\d])\s*-\s*(?=[\w\d])", " trừ ", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", " nhân ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,")


def physics_value_speech(value):
    text = expression_speech_text(value)
    replacements = {
        "Ω": "ôm",
        "ohm": "ôm",
        "m trên s bình phương": "mét trên giây bình phương",
        "m/s bình phương": "mét trên giây bình phương",
        "m trên s": "mét trên giây",
        "m/s": "mét trên giây",
        "rad trên s": "ra đi an trên giây",
        "rad/s": "ra đi an trên giây",
    }
    for source, target in replacements.items():
        text = re.sub(rf"(?<!\w){re.escape(source)}(?!\w)", target, text)
    unit_words = {
        "kg": "ki lô gam",
        "N": "niu tơn",
        "V": "vôn",
        "A": "ampe",
        "W": "oát",
        "J": "jun",
        "Hz": "héc",
        "cm": "xen ti mét",
        "m": "mét",
        "rad": "ra đi an",
        "s": "giây",
    }
    for unit, word in unit_words.items():
        text = re.sub(rf"(?<=\d)\s*{re.escape(unit)}\b", f" {word}", text)
    text = text.replace("mét trên giây bình phương", "mét trên giây bình phương")
    return re.sub(r"\s+", " ", text).strip()


PHYSICS_VARIABLE_NAMES = {
    "m": "khối lượng m",
    "A": "biên độ A",
    "F": "lực F",
    "a": "gia tốc a",
    "v": "vận tốc v",
    "U": "hiệu điện thế U",
    "I": "cường độ dòng điện I",
    "R": "điện trở R",
    "P": "công suất P",
    "Q": "nhiệt lượng Q",
    "T": "chu kì T",
    "f": "tần số f",
    "x": "li độ x",
    "omega": "tần số góc omega",
    "phi": "pha ban đầu phi",
    "lambda": "bước sóng lambda",
}


def physics_symbol_name(symbol):
    return PHYSICS_VARIABLE_NAMES.get(symbol, symbol)


def physics_expression_speech(text):
    value = str(text or "").strip()
    value = re.sub(r"\bfrac(\d)(0,\d+)\b", r"\1/\2", value)
    value = re.sub(r"\bfrac(\d+,\d)(\d+)\b", r"\1/\2", value)
    value = value.replace("ω", "omega").replace("φ", "phi").replace("π", "pi").replace("λ", "lambda")
    value = value.replace("\\cdot", " nhân ").replace("·", " nhân ")
    value = re.sub(r"\bA(?=cos|sin)", "A nhân ", value)
    value = value.replace("Δt", "độ biến thiên nhiệt độ").replace("\\Delta t", "độ biến thiên nhiệt độ")
    value = value.replace("ma", "m nhân a")
    value = value.replace("mc", "m nhân c")
    value = re.sub(r"(?<=\d)(?=[A-Za-z])", " nhân ", value)
    value = expression_speech_text(value)
    value = physics_value_speech(value)
    value = re.sub(r"(?<=\d)\s+trên\s+(?=\d)", " chia cho ", value)
    for symbol in sorted(PHYSICS_VARIABLE_NAMES, key=len, reverse=True):
        value = re.sub(rf"\b{re.escape(symbol)}\b", physics_symbol_name(symbol), value)
    value = value.replace("mét trên giây bình phương", "mét mỗi giây bình phương")
    value = value.replace("mét trên giây", "mét mỗi giây")
    value = value.replace("ra đi an trên giây", "ra đi an mỗi giây")
    value = value.replace(" trên ", " chia cho ")
    return re.sub(r"\s+", " ", value).strip()


def physics_line_speech_text(line):
    text = re.sub(r"\s+", " ", str(line or "")).strip()
    if not text:
        return ""
    text = text.replace("\\Omega", "Ω").replace("Ω", "Ω")
    text = text.replace("m/s²", "m/s^2").replace("m/s2", "m/s^2")

    exact_formulas = {
        "F = ma": "Lực F bằng khối lượng m nhân gia tốc a",
        "F=ma": "Lực F bằng khối lượng m nhân gia tốc a",
        "a = F/m": "Gia tốc a bằng lực F chia cho khối lượng m",
        "a=F/m": "Gia tốc a bằng lực F chia cho khối lượng m",
        "I = U/R": "Cường độ dòng điện I bằng hiệu điện thế U chia cho điện trở R",
        "I=U/R": "Cường độ dòng điện I bằng hiệu điện thế U chia cho điện trở R",
        "U = I R": "Hiệu điện thế U bằng cường độ dòng điện I nhân điện trở R",
        "U=IR": "Hiệu điện thế U bằng cường độ dòng điện I nhân điện trở R",
        "P = U I": "Công suất P bằng hiệu điện thế U nhân cường độ dòng điện I",
        "P=UI": "Công suất P bằng hiệu điện thế U nhân cường độ dòng điện I",
        "Q = mcΔt": "Nhiệt lượng Q bằng khối lượng m nhân nhiệt dung riêng c nhân độ biến thiên nhiệt độ",
        "Q=mcΔt": "Nhiệt lượng Q bằng khối lượng m nhân nhiệt dung riêng c nhân độ biến thiên nhiệt độ",
    }
    compact = re.sub(r"\s+", " ", text)
    if compact in exact_formulas:
        return exact_formulas[compact]

    unit_after_number_pattern = r"\d+(?:[.,]\d+)?\s*(kg|N|V|A|Ω|ohm|W|J|Hz|cm|rad|s|m/s\^?2|m/s)\b"
    value_match = re.match(r"^([A-Za-zωφλ]+)\s*=\s*(.+?)\s*$", text)
    if value_match:
        symbol, value = value_match.groups()
        symbol = symbol.replace("ω", "omega").replace("φ", "phi").replace("λ", "lambda")
        if symbol in PHYSICS_VARIABLE_NAMES and (
            re.search(unit_after_number_pattern, text)
            or "/" in text
            or re.search(r"\b[UFIRPQTfavmAx]\b|ω|φ|λ|omega|phi|lambda", value)
            or any(func in value for func in ("cos", "sin"))
        ):
            return f"{physics_symbol_name(symbol)} bằng {physics_expression_speech(value)}"

    if re.search(unit_after_number_pattern, text) or re.search(r"\b[UFIRPQTfavmAx]\s*=", text) or re.search(r"[ωφλ]\s*=", text):
        return physics_expression_speech(text)
    return ""


def math_line_speech_text(line):
    text = re.sub(r"\s+", " ", str(line or "")).strip()
    if not text:
        return ""
    physics_text = physics_line_speech_text(text)
    if physics_text:
        return physics_text
    text = text.replace(" in ", " ∈ ")
    coordinate = re.match(r"^([A-Z])\(([^;()]+);([^()]+)\)(?:,\s*(.*))?$", text)
    if coordinate:
        point, x_value, y_value, tail = coordinate.groups()
        spoken = (
            f"Điểm {point} có tọa độ x bằng {expression_speech_text(x_value)}, "
            f"y bằng {expression_speech_text(y_value)}"
        )
        if tail:
            spoken += f"; với điều kiện {math_line_speech_text(tail)}"
        return spoken
    if re.match(r"^[A-Z](?:,\s*[A-Z]){2,}\s+thẳng hàng$", text):
        letters = " ".join(re.findall(r"[A-Z]", text))
        return f"Các điểm {letters} thẳng hàng"
    circle_match = re.match(r"^([A-Z])\s*(?:∈|in)\s*\(([A-Z])\)$", text)
    if circle_match:
        return f"Điểm {circle_match.group(1)} thuộc đường tròn tâm {circle_match.group(2)}"
    text = re.sub(r"\b([A-Z]{2})\b", lambda match: "đoạn " + " ".join(match.group(1)), text)
    text = expression_speech_text(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def full_solution_chunk_speech(chunk, part_index=None, total_parts=None):
    items = full_solution_items({"slide_text": chunk})
    if not items:
        return math_line_speech_text(chunk)
    prefix = "Tóm tắt lời giải"
    if part_index is not None and total_parts and total_parts > 1:
        prefix += f", phần {part_index} trên {total_parts}"
    sentences = [prefix + "."]
    for item in items[:4]:
        title = math_line_speech_text(item.get("title") or "")
        lines = [math_line_speech_text(line) for line in item.get("lines", [])[:3]]
        lines = [line for line in lines if line]
        body = ". ".join(lines)
        if body:
            sentences.append(f"Mục {item.get('index')}: {title}. {body}.")
        elif title:
            sentences.append(f"Mục {item.get('index')}: {title}.")
    return " ".join(sentences)


def needs_symbol_speech(line):
    text = str(line or "").strip()
    if not text:
        return False
    return bool(
        re.match(r"^[A-Za-zωφλ]+\s*=", text)
        or re.match(r"^[A-Z]\([^()]+;[^()]+\)", text)
        or re.match(r"^[A-Z](?:,\s*[A-Z]){2,}\s+thẳng hàng$", text)
        or re.match(r"^[A-Z]\s+(?:in|∈)\s+\([A-Z]\)$", text)
        or re.search(r"[=⇒≤≥≠≈⊥]|\\frac|\\sqrt|\bfrac\d", text)
    )


def narration_speech_text(value):
    raw_text = str(value or "").strip()
    if raw_text.lower().startswith("tóm tắt lời giải"):
        return re.sub(r"\s+", " ", raw_text).strip()
    text = narration_display_text(value)
    if text.lower().startswith("tóm tắt lời giải"):
        return re.sub(r"\s+", " ", text).strip()
    text = "\n".join(
        math_line_speech_text(line) if needs_symbol_speech(line) else line
        for line in text.splitlines()
    )
    replacements = {
        "→": " vectơ ",
        "·": " nhân vô hướng ",
        "≤": " nhỏ hơn hoặc bằng ",
        "≥": " lớn hơn hoặc bằng ",
        "≠": " khác ",
        "≈": " xấp xỉ ",
        "√": " căn ",
        "²": " bình phương ",
        "³": " lập phương ",
        "ω": " omega ",
        "φ": " phi ",
        "π": " pi ",
        "λ": " lambda ",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text).strip()


def formula_lines(value):
    text = latex_to_text(value)
    if not text:
        return []
    lines = []
    for line in text.splitlines():
        parts = re.split(r"\s*(?:&&|&)\s*", line)
        for part in parts:
            part = part.strip()
            if part:
                lines.append(part)
    return lines


def history_illustration_markup(scene):
    image_ref = str(scene.get("image_ref") or "").strip().replace("\\", "/")
    caption = escape(str(scene.get("image_caption") or "Ảnh minh họa lịch sử"))
    if image_ref:
        safe_src = escape(image_ref, quote=True)
        return f'''
          <figure class="history-photo">
            <img src="{safe_src}" alt="{caption}">
            <figcaption>{caption}</figcaption>
          </figure>
        '''
    return f'''
      <figure class="history-photo history-photo-empty">
        <div>TƯ LIỆU</div>
        <figcaption>{caption}</figcaption>
      </figure>
    '''


def history_scene_html(scene, index, template_id="history_archive"):
    theme = get_design_template(template_id)
    bg = theme["bg"]
    card = theme["card"]
    primary = theme["primary"]
    accent = theme["accent"]
    accent_light = theme["accent_light"]
    text_color = theme["text"]
    muted = theme["muted"]
    formula_bg = theme["formula_bg"]
    border = theme["border"]
    title = escape(str(scene.get("title") or f"Phần {index + 1}"))
    section_label = escape(str(scene.get("section_label") or f"Phần {index + 1:02d}"))
    narration = escape(scene_display_text(scene) or " ")
    visual = scene_visual_markup(scene, theme)
    illustration = history_illustration_markup(scene)
    newspaper = template_id == "history_newspaper_1990"
    scene_class = "scene history-scene newspaper-scene" if newspaper else "scene history-scene"
    width, height = VIDEO_SIZE

    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>History Scene {index + 1}</title>
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{ width: {width}px; height: {height}px; margin: 0; overflow: hidden; }}
    body {{
      background: {bg};
      color: {text_color};
      font-family: Arial, Helvetica, sans-serif;
    }}
    .history-scene {{
      width: {width}px;
      height: {height}px;
      padding: 34px 38px 30px;
      display: grid;
      grid-template-columns: minmax(0, 0.9fr) 490px;
      grid-template-rows: auto 1fr auto;
      gap: 18px 20px;
      background:
        repeating-linear-gradient(0deg, rgba(31,26,23,0.035) 0 1px, transparent 1px 7px),
        linear-gradient(180deg, {card} 0%, {bg} 100%);
      border: 12px solid {bg};
    }}
    .newspaper-scene {{
      border: 10px double {primary};
      background:
        repeating-linear-gradient(90deg, rgba(31,26,23,0.04) 0 1px, transparent 1px 34px),
        repeating-linear-gradient(0deg, rgba(31,26,23,0.03) 0 1px, transparent 1px 8px),
        {card};
    }}
    .history-kicker {{
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      padding-bottom: 12px;
      border-bottom: 4px solid {primary};
      color: {primary};
      font-family: Arial, Helvetica, sans-serif;
      font-weight: 900;
      text-transform: uppercase;
      font-size: 20px;
    }}
    .history-date {{
      color: {accent};
      font-family: Arial, Helvetica, sans-serif;
      font-size: 16px;
      font-weight: 800;
    }}
    .history-content {{
      min-width: 0;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      gap: 18px;
      align-self: stretch;
    }}
    h1 {{
      margin: 0;
      color: {primary};
      font-family: Arial, Helvetica, sans-serif;
      font-size: 37px;
      line-height: 1.08;
      letter-spacing: 0;
      font-weight: 900;
      text-transform: uppercase;
    }}
    .history-copy {{
      min-height: 0;
      padding: 20px 22px;
      border-left: 9px solid {accent};
      background: rgba(255,255,255,0.38);
      color: {text_color};
      font-family: Arial, Helvetica, sans-serif;
      font-size: 22px;
      line-height: 1.34;
      white-space: pre-line;
      overflow: hidden;
      overflow-wrap: anywhere;
    }}
    .history-copy::first-line {{
      color: {accent};
      font-weight: 900;
    }}
    .history-side {{
      min-width: 0;
      min-height: 0;
      display: grid;
      grid-template-rows: 228px minmax(0, 1fr);
      gap: 12px;
      align-self: stretch;
    }}
    .history-photo {{
      margin: 0;
      min-width: 0;
      min-height: 0;
      border: 3px solid {primary};
      background: {formula_bg};
      padding: 10px;
      box-shadow: 8px 8px 0 {accent_light};
    }}
    .history-photo img {{
      width: 100%;
      height: 166px;
      object-fit: cover;
      display: block;
      filter: sepia(0.28) contrast(1.05);
      background: {border};
    }}
    .history-photo-empty {{
      height: 228px;
      display: grid;
      place-items: center;
      color: {muted};
      font-size: 38px;
      font-weight: 900;
      text-align: center;
    }}
    figcaption {{
      margin-top: 9px;
      color: {muted};
      font-family: Arial, Helvetica, sans-serif;
      font-size: 15px;
      line-height: 1.25;
      font-weight: 700;
    }}
    .visual {{
      min-width: 0;
      min-height: 0;
      border: 2px solid {border};
      background: {formula_bg};
      display: grid;
      place-items: center;
      padding: 8px;
      overflow: hidden;
    }}
    .history-svg {{
      width: 100%;
      height: 100%;
      max-height: 340px;
      font-family: Arial, Helvetica, sans-serif;
    }}
    .footer {{
      grid-column: 1 / -1;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 2px solid {border};
      padding-top: 12px;
      color: {muted};
      font-family: Arial, Helvetica, sans-serif;
      font-size: 16px;
      font-weight: 700;
    }}
    .brand {{ color: {accent}; }}
  </style>
</head>
<body>
  <main class="{scene_class}">
    <div class="history-kicker">
      <span>{section_label}</span>
      <span class="history-date">Lesson Loom History</span>
    </div>
    <section class="history-content">
      <h1 class="fit-text">{title}</h1>
      <div class="history-copy fit-text">{narration}</div>
    </section>
    <aside class="history-side">
      {illustration}
      <div class="visual">{visual}</div>
    </aside>
    <footer class="footer">
      <span class="brand">Tư liệu học tập</span>
      <span>Video lịch sử có minh họa</span>
    </footer>
  </main>
  <script>
    function fitText() {{
      const nodes = document.querySelectorAll('.fit-text');
      for (const node of nodes) {{
        let size = parseFloat(getComputedStyle(node).fontSize);
        const minSize = node.tagName === 'H1' ? 28 : 15;
        let guard = 0;
        while ((node.scrollHeight > node.clientHeight || node.scrollWidth > node.clientWidth) && size > minSize && guard < 30) {{
          size -= 1.5;
          if (size < minSize) size = minSize;
          node.style.fontSize = size + 'px';
          guard += 1;
        }}
      }}
    }}
    window.addEventListener('load', () => {{
      setTimeout(fitText, 50);
      setTimeout(fitText, 350);
    }});
  </script>
</body>
</html>"""


def scene_html(scene, index, template_id="studio"):
    html = _scene_html_base(scene, index, template_id)
    if str(template_id).startswith('history_') or is_history_subject(scene.get('subject')):
        return html
    return polish_html(html, get_design_template(template_id), scene)


def _scene_html_base(scene, index, template_id="studio"):
    if str(template_id or "").startswith("history_") or is_history_subject(scene.get("subject")) or scene.get("image_ref"):
        return history_scene_html(scene, index, template_id=template_id)
    theme = get_design_template(template_id)
    bg = theme["bg"]
    card = theme["card"]
    primary = theme["primary"]
    accent = theme["accent"]
    accent_light = theme["accent_light"]
    text_color = theme["text"]
    muted = theme["muted"]
    formula_bg = theme["formula_bg"]
    border = theme["border"]
    title = escape(str(scene.get("title") or f"Bước {index + 1}"))
    raw_latex = str(scene.get("latex") or "")
    latex = escape(latex_for_katex(raw_latex))
    formula_text = escape(latex_to_text(scene.get("latex")))
    visual = scene_visual_markup(scene, theme)
    has_formula = "true" if latex else "false"
    layout = str(scene.get("layout") or "")
    is_full_solution = layout == "full_solution"
    narration = full_solution_markup(scene) if is_full_solution else slide_markup(scene_display_text(scene) or " ")
    layout_class = " full-solution" if layout == "full_solution" else ""
    has_visual = bool(scene.get("geometry") or scene.get("visual") or (scene.get("diagram") and visual))
    if not has_visual and not is_full_solution:
        layout_class += " text-only"
    visual_html = "" if is_full_solution or not has_visual else f'<aside class="visual">{visual}</aside>'
    width, height = VIDEO_SIZE

    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Scene {index + 1}</title>
  <link rel="stylesheet" href="{(BASE_DIR / 'static/vendor/katex/katex.min.css').as_uri()}">
  <script defer src="{(BASE_DIR / 'static/vendor/katex/katex.min.js').as_uri()}"></script>
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{ width: {width}px; height: {height}px; margin: 0; overflow: hidden; }}
    body {{
      background: {bg};
      color: {text_color};
      font-family: Arial, Helvetica, sans-serif;
    }}
    .scene {{
      width: {width}px;
      height: {height}px;
      padding: 38px;
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.85fr);
      grid-template-rows: auto 1fr auto;
      gap: 22px 28px;
      background:
        radial-gradient(circle at 91% 13%, {accent_light} 0 110px, transparent 111px),
        linear-gradient(180deg, {card} 0%, {bg} 100%);
      border: 10px solid {bg};
    }}
    .scene.full-solution, .scene.text-only {{
      grid-template-columns: 1fr;
    }}
    .scene.full-solution .content {{
      max-width: 1120px;
      gap: 18px;
    }}
    .scene.full-solution .narration {{
      font-size: 22px;
      line-height: 1.28;
      overflow: hidden;
    }}
    .solution-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      align-content: start;
    }}
    .solution-card {{
      min-width: 0;
      display: grid;
      grid-template-columns: 46px minmax(0, 1fr);
      gap: 12px;
      padding: 14px 16px;
      border: 1px solid {border};
      border-left: 6px solid {accent};
      border-radius: 8px;
      background: {card};
      box-shadow: 0 10px 24px rgba(43, 76, 126, 0.06);
    }}
    .solution-index {{
      width: 36px;
      height: 36px;
      border-radius: 999px;
      display: grid;
      place-items: center;
      background: {primary};
      color: #FFFFFF;
      font-size: 15px;
      font-weight: 800;
    }}
    .solution-body {{
      min-width: 0;
    }}
    .solution-card h2 {{
      margin: 0 0 8px;
      color: {primary};
      font-size: 0.92em;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    .solution-lines {{
      display: grid;
      gap: 5px;
    }}
    .solution-line {{
      color: {text_color};
      font-size: 0.8em;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }}
    .solution-line.formula-line {{
      padding: 5px 8px;
      border-radius: 6px;
      background: {formula_bg};
      color: {primary};
      font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
      font-weight: 700;
    }}
    .solution-line.result-line {{
      background: #FFF7E0;
      color: #7C2D12;
    }}
    .kicker {{
      grid-column: 1 / -1;
      color: {accent};
      font: 700 18px/1.1 "Arial", sans-serif;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .content {{
      min-width: 0;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
      gap: 22px;
    }}
    h1 {{
      margin: 0;
      color: {primary};
      font-size: 48px;
      line-height: 1.08;
      letter-spacing: 0;
    }}
    .narration {{
      min-height: 0;
      color: {text_color};
      font-size: 27px;
      line-height: 1.45;
      white-space: pre-line;
      overflow: hidden;
    }}
    .formula {{
      min-height: 86px;
      padding: 18px 22px;
      border-left: 7px solid {accent};
      background: {formula_bg};
      color: {primary};
      display: flex;
      align-items: center;
      overflow: hidden;
      font-size: 28px;
      font-weight: 700;
      line-height: 1.25;
      white-space: pre-line;
    }}
    .formula.formula-fallback {{
      font-family: Arial, Helvetica, sans-serif;
      font-size: 23px;
      color: {primary};
    }}
    .formula[data-has-formula="false"] {{
      display: none;
    }}
    .visual {{
      min-width: 0;
      min-height: 0;
      border: 2px solid {border};
      background: {card};
      border-radius: 8px;
      display: grid;
      place-items: center;
      padding: 28px;
      overflow: hidden;
    }}
    .geometry-svg {{
      width: 100%;
      height: 100%;
      max-height: 520px;
      font-family: Arial, Helvetica, sans-serif;
    }}
    .physics-svg {{
      max-height: 500px;
    }}
    .empty-visual {{
      width: 100%;
      height: 100%;
      display: grid;
      place-items: center;
      color: {accent};
      font-size: 42px;
      font-weight: 800;
      border: 3px dashed {accent_light};
      border-radius: 8px;
    }}
    .footer {{
      grid-column: 1 / -1;
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: {muted};
      font-size: 18px;
      border-top: 1px solid {border};
      padding-top: 16px;
    }}
    .brand {{ color: {primary}; font-weight: 700; }}
    .history-svg {{
      width: 100%;
      height: 100%;
      max-height: 520px;
      font-family: Arial, Helvetica, sans-serif;
    }}
    .formula .katex {{ font-size: 0.92em; }}
    .katex-display {{ margin: 0; width: 100%; }}
  </style>
</head>
<body>
  <main class="scene{layout_class}">
    <div class="kicker">BƯỚC {index + 1:02d}</div>
    <section class="content">
      <h1 class="fit-text">{title}</h1>
      <div class="narration fit-text">{narration}</div>
      <div class="formula" data-has-formula="{has_formula}" data-latex="{latex}" data-fallback="{formula_text}"></div>
    </section>
    {visual_html}
    <footer class="footer">
      <span class="brand">Lesson Loom</span>
      <span>Video bài giảng tự động</span>
    </footer>
  </main>
  <script>
    function renderFormula() {{
      const box = document.querySelector('.formula');
      const latex = box.dataset.latex || '';
      if (!latex) {{
        box.textContent = ' ';
        return;
      }}
      box.classList.remove('formula-fallback');
      if (window.katex) {{
        try {{
          window.katex.render(latex, box, {{ throwOnError: true, displayMode: true }});
          return;
        }} catch (error) {{}}
      }}
      box.classList.add('formula-fallback');
      box.textContent = box.dataset.fallback || latex;
    }}
    function fitText() {{
      const nodes = document.querySelectorAll('.fit-text, .formula');
      for (const node of nodes) {{
        let size = parseFloat(getComputedStyle(node).fontSize);
        let guard = 0;
        while ((node.scrollHeight > node.clientHeight + 2 || node.scrollWidth > node.clientWidth + 2) && size > 22 && guard < 28) {{
          size = Math.max(22, size - 1.5);
          node.style.fontSize = size + 'px';
          guard += 1;
        }}
      }}
    }}
    window.addEventListener('load', () => {{
      renderFormula();
      setTimeout(fitText, 50);
      setTimeout(fitText, 350);
    }});
    setTimeout(() => {{
      renderFormula();
      fitText();
    }}, 900);
  </script>
</body>
</html>"""


def render_scene_html(scene, index, output_path, template_id="studio"):
    output_path.write_text(scene_html(scene, index, template_id=template_id), encoding="utf-8")


def check_slide_layout(page):
    issues = page.evaluate("""() => {
      if (!document.querySelector('main[data-kind]')) return [];
      return [...document.querySelectorAll('.fit-text,.formula')]
        .filter(n => n.clientHeight && (n.scrollHeight > n.clientHeight + 2 || n.scrollWidth > n.clientWidth + 2))
        .map(n => n.className);
    }""")
    if issues:
        raise ValueError('Slide quá nhiều chữ/công thức. Hãy rút gọn hoặc chia thành nhiều bước.')


def render_scene_png_with_playwright(html_path, output_path):
    if importlib.util.find_spec("playwright") is None:
        return False
    try:
        from playwright.sync_api import sync_playwright

        width, height = VIDEO_SIZE
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel=os.getenv("PLAYWRIGHT_CHANNEL") or None)
            try:
                page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                page.goto(html_path.resolve().as_uri(), wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1200)
                page.evaluate('document.fonts.ready')
                check_slide_layout(page)
                page.screenshot(path=str(output_path), type="png")
            finally:
                browser.close()
        return True
    except Exception as e:
        print(f"Playwright render fallback for {html_path.name}: {e}")
        return False


def estimate_scene_duration(scene):
    narration = narration_speech_text(scene.get("narration") or "")
    return max(4.0, min(22.0, len(narration) / 16.0))


def split_text_chunks(text, max_chars=360):
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    source_lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]
    source_lines = [line for line in source_lines if line]
    text = "\n".join(source_lines)
    if len(text) <= max_chars:
        return [text] if text else [""]

    sentences = []
    for line in source_lines:
        parts = re.split(r"(?<=[.!?。！？])\s+", line)
        for part_index, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            if part_index == 0 and sentences:
                sentences.append("\n" + part)
            else:
                sentences.append(part)
    chunks = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        separator = "" if sentence.startswith("\n") or not current else " "
        candidate = f"{current}{separator}{sentence}".strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            chunks.append(current)
            current = sentence.lstrip()
    if current:
        chunks.append(current)

    refined = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            refined.append(chunk)
            continue
        words = chunk.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= max_chars or not current:
                current = candidate
            else:
                refined.append(current)
                current = word
        if current:
            refined.append(current)
    return refined or [text]


def split_solution_chunks(text, max_lines=9, max_chars=520):
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    if not lines:
        return [""]
    chunks = []
    current = []
    current_chars = 0
    for line in lines:
        line_len = len(line)
        if current and (len(current) >= max_lines or current_chars + line_len > max_chars):
            chunks.append("\n".join(current))
            current = []
            current_chars = 0
        current.append(line)
        current_chars += line_len + 1
    if current:
        chunks.append("\n".join(current))
    return chunks or [str(text or "")]


def is_history_scene(scene):
    if is_history_subject((scene or {}).get("subject")):
        return True
    if str((scene or {}).get("section_label") or "").lower().startswith("phần"):
        return True
    return bool((scene or {}).get("image_ref")) and isinstance((scene or {}).get("visual"), dict)


def expand_long_scenes(scenes):
    expanded = []
    for scene in scenes:
        is_full_solution = str(scene.get("layout") or "") == "full_solution"
        history_scene = is_history_scene(scene)
        if is_full_solution:
            source_text = scene_display_text(scene)
        elif history_scene:
            source_text = restore_history_text(narration_display_text(scene.get("narration") or scene_display_text(scene)))
        else:
            source_text = narration_display_text(scene.get("narration") or "")
        if is_full_solution:
            chunks = split_solution_chunks(source_text)
        elif history_scene:
            chunks = split_text_chunks(source_text, max_chars=500)
        else:
            chunks = split_text_chunks(source_text)
        if len(chunks) == 1:
            clone = dict(scene)
            clone["slide_text"] = scene_display_text(scene)
            clone["narration"] = source_text if history_scene else full_solution_chunk_speech(source_text) if is_full_solution else source_text
            expanded.append(clone)
            continue
        total = len(chunks)
        for chunk_index, chunk in enumerate(chunks):
            clone = dict(scene)
            clone["title"] = f"{scene.get('title', 'Bước giải')} ({chunk_index + 1}/{total})"
            if is_full_solution:
                clone["slide_text"] = chunk
                clone["narration"] = full_solution_chunk_speech(chunk, chunk_index + 1, total)
            elif history_scene:
                clone["title"] = f"{clean_history_title(scene.get('title', 'Phần lịch sử'), chunk_index + 1)} ({chunk_index + 1}/{total})"
                clone["slide_text"] = chunk
                clone["narration"] = chunk
            else:
                clone["narration"] = chunk
                clone["slide_text"] = scene_display_text(scene)
            clone["geometry"] = scene.get("geometry")
            clone["diagram"] = scene.get("diagram")
            clone["visual"] = scene.get("visual")
            clone["latex"] = scene.get("latex")
            clone["section_label"] = scene.get("section_label")
            clone["image_ref"] = scene.get("image_ref")
            clone["image_caption"] = scene.get("image_caption")
            expanded.append(clone)
    return expanded


def scene_svg(scene, index):
    geometry = scene.get("geometry") or {}
    points = geometry.get("points", {})
    point_values = list(points.values())
    if point_values:
        lines = []
        for name, point in points.items():
            x, y = 170 + point[0] * 90, 360 - point[1] * 60
            lines.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#3AAFA9"/><text x="{x + 12}" y="{y - 12}" fill="#1F2937" font-family="Arial" font-size="24" font-weight="bold">{name}</text>')
        if len(point_values) >= 3:
            coords = " ".join(f"{170 + p[0] * 90},{360 - p[1] * 60}" for p in point_values)
            lines.insert(0, f'<polyline points="{coords}" fill="none" stroke="#2B4C7E" stroke-width="4"/>')
        geometry_markup = "".join(lines)
    else:
        geometry_markup = ""
    formula = escape(latex_to_text(scene.get("latex") or ""))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
<rect width="1920" height="1080" fill="#F3F4F6"/>
<rect x="60" y="60" width="1800" height="960" rx="20" fill="#FFFFFF" stroke="#DEF2F1" stroke-width="4"/>
<circle cx="1740" cy="140" r="160" fill="#DEF2F1"/>
<text x="120" y="150" font-family="Arial" font-size="28" font-weight="bold" fill="#3AAFA9">BƯỚC {index + 1:02d}</text>
<text x="120" y="240" font-family="Arial" font-size="64" font-weight="bold" fill="#2B4C7E">{scene.get('title', '')}</text>
<foreignObject x="120" y="310" width="1100" height="300"><div xmlns="http://www.w3.org/1999/xhtml" style="font: 36px/1.5 Arial, sans-serif; color:#1F2937">{scene_display_text(scene)}</div></foreignObject>
<text x="120" y="780" font-family="Georgia" font-size="52" fill="#2B4C7E" font-weight="bold">{formula}</text>
<g>{geometry_markup}</g></svg>'''


@lru_cache(maxsize=96)
def cached_font(name, size):
    font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    path = font_dir / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    bundled = BASE_DIR / 'static/fonts/video' / ('NotoSans-Bold.ttf' if 'bd' in name.lower() else 'NotoSans-Regular.ttf')
    if bundled.exists():
        return ImageFont.truetype(str(bundled), size)
    linux_font = Path('/usr/share/fonts/truetype/dejavu') / ('DejaVuSans-Bold.ttf' if 'bd' in name.lower() else 'DejaVuSans.ttf')
    return ImageFont.truetype(str(linux_font), size) if linux_font.exists() else ImageFont.load_default(size=size)


def font_loader():
    return cached_font


def wrap_text(draw, text, font, max_width):
    lines = []
    for paragraph in str(text or "").splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if draw.textlength(candidate, font=font) <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def line_height(font):
    bbox = font.getbbox("Ag")
    return max(1, bbox[3] - bbox[1])


def fit_wrapped_text(draw, text, font_name, max_size, min_size, box_width, box_height, spacing=6):
    font = font_loader()
    for size in range(max_size, min_size - 1, -1):
        candidate_font = font(font_name, size)
        lines = wrap_text(draw, text, candidate_font, box_width)
        total_height = len(lines) * line_height(candidate_font) + max(0, len(lines) - 1) * spacing
        longest = max([draw.textlength(line, font=candidate_font) for line in lines] or [0])
        if total_height <= box_height and longest <= box_width:
            return candidate_font, lines, spacing
    candidate_font = font(font_name, min_size)
    return candidate_font, wrap_text(draw, text, candidate_font, box_width), max(2, spacing - 2)


def fit_formula_text(draw, lines, font_name, max_size, min_size, box_width, box_height, spacing=5):
    font = font_loader()
    source_lines = [str(line or "").strip() for line in lines if str(line or "").strip()]
    if not source_lines:
        return font(font_name, min_size), [], spacing
    for size in range(max_size, min_size - 1, -1):
        candidate_font = font(font_name, size)
        rendered_lines = []
        for line in source_lines:
            rendered_lines.extend(wrap_text(draw, line, candidate_font, box_width))
        total_height = len(rendered_lines) * line_height(candidate_font) + max(0, len(rendered_lines) - 1) * spacing
        longest = max([draw.textlength(line, font=candidate_font) for line in rendered_lines] or [0])
        if total_height <= box_height and longest <= box_width:
            return candidate_font, rendered_lines, spacing
    candidate_font = font(font_name, min_size)
    rendered_lines = []
    for line in source_lines:
        rendered_lines.extend(wrap_text(draw, line, candidate_font, box_width))
    return candidate_font, rendered_lines, max(2, spacing - 2)


def reveal_parts(parts, reveal_ratio):
    total = sum(len(part) for part in parts)
    visible = max(0, min(total, round(total * reveal_ratio)))
    result = []
    for part in parts:
        chunk = part[:visible]
        result.append(chunk)
        visible -= len(chunk)
        if visible < 0:
            visible = 0
    return result


def split_reveal_units(text):
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]
    raw_lines = [line for line in raw_lines if line]
    if not raw_lines:
        return []
    refined = []
    for line_index, line in enumerate(raw_lines):
        units = re.split(r"(?<=[.!?。！？])\s+", line)
        first_unit_in_line = True
        for unit in units:
            unit = unit.strip()
            if not unit:
                continue
            chunks = [unit] if len(unit) <= 150 else re.split(r"(?<=[,;:])\s+", unit)
            current = ""
            for chunk in chunks:
                candidate = f"{current} {chunk}".strip()
                if len(candidate) <= 150 or not current:
                    current = candidate
                else:
                    prefix = "\n" if line_index > 0 and first_unit_in_line else ""
                    refined.append(prefix + current)
                    first_unit_in_line = False
                    current = chunk
            if current:
                prefix = "\n" if line_index > 0 and first_unit_in_line else ""
                refined.append(prefix + current)
                first_unit_in_line = False
    return refined


def reveal_by_units(units, reveal_ratio):
    if not units:
        return ""
    visible_count = max(1, min(len(units), int(len(units) * reveal_ratio + 0.999)))
    text = ""
    for unit in units[:visible_count]:
        if unit.startswith("\n"):
            text = text.rstrip() + "\n" + unit.lstrip()
        elif not text:
            text = unit
        else:
            text += " " + unit
    return text


def reveal_formula_lines(lines, reveal_ratio):
    if not lines:
        return []
    visible_count = max(1, min(len(lines), int(len(lines) * reveal_ratio + 0.999)))
    return lines[:visible_count]


def draw_multiline(draw, xy, lines, font, fill, spacing):
    x, y = xy
    step = line_height(font) + spacing
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += step


def draw_circle_diameter_geometry(draw, geometry, font, theme, box, reveal_ratio=1.0):
    points = coerce_points(geometry.get("points", {}))
    if not points:
        return False

    draw.rounded_rectangle(box, radius=10, outline=theme["border"], width=2, fill=theme["formula_bg"])
    diameter = geometry.get("diameter") or ["A", "B"]
    center_label = geometry.get("center") or "O"
    a_label = diameter[0] if len(diameter) > 0 else "A"
    b_label = diameter[1] if len(diameter) > 1 else "B"

    xs = [point[0] for point in points.values()]
    ys = [point[1] for point in points.values()]
    min_x, max_x = min(xs + [-1.35]), max(xs + [1.35])
    min_y, max_y = min(ys + [-1.15]), max(ys + [1.15])
    pad_x = max(0.25, (max_x - min_x) * 0.12)
    pad_y = max(0.25, (max_y - min_y) * 0.12)
    min_x -= pad_x
    max_x += pad_x
    min_y -= pad_y
    max_y += pad_y
    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)

    def to_px(x, y):
        px = box[0] + 24 + (x - min_x) / span_x * (box[2] - box[0] - 48)
        py = box[3] - 24 - (y - min_y) / span_y * (box[3] - box[1] - 48)
        return px, py

    def line(name1, name2, fill=None, width=3):
        if name1 in points and name2 in points:
            draw.line((*to_px(*points[name1]), *to_px(*points[name2])), fill=fill or theme["primary"], width=width)

    ox, oy = points.get(center_label, [0.0, 0.0])
    left = to_px(ox - 1, oy + 1)
    right = to_px(ox + 1, oy - 1)
    draw.ellipse((left[0], left[1], right[0], right[1]), outline=theme["primary"], width=3)

    line(a_label, b_label, width=3)
    line(a_label, "C", width=3)
    line(b_label, "C", width=3)
    if "D" in points:
        line(a_label, "D", fill=theme["muted"], width=2)
        line("C", "D", fill=theme["accent"], width=3)
    if "E" in points:
        line(a_label, "E", width=3)
        line(b_label, "E", fill=theme["accent"], width=2)
    if "F" in points:
        line(b_label, "F", width=3)
        line(a_label, "F", fill=theme["accent"], width=2)

    # Tangent hints at the three key points.
    if a_label in points:
        ax, ay = points[a_label]
        draw.line((*to_px(ax, min_y + pad_y * 0.5), *to_px(ax, max_y - pad_y * 0.5)), fill=theme["accent"], width=1)
    if b_label in points:
        bx, by = points[b_label]
        draw.line((*to_px(bx, min_y + pad_y * 0.5), *to_px(bx, max_y - pad_y * 0.5)), fill=theme["accent"], width=1)
    if "C" in points and "D" in points:
        line("C", "D", fill=theme["accent"], width=2)

    for name, (x, y) in points.items():
        px, py = to_px(x, y)
        dot_size = 5 if name == center_label else 7
        draw.ellipse((px - dot_size, py - dot_size, px + dot_size, py + dot_size), fill=theme["accent"], outline=theme["primary"], width=2)
        draw.text((px + 9, py - 20), name, font=font("arialbd.ttf", 18), fill=theme["text"])
    return True


def draw_arrow(draw, start, end, fill, width=5):
    draw.line((*start, *end), fill=fill, width=width)
    x1, y1 = start
    x2, y2 = end
    angle = math.atan2(y2 - y1, x2 - x1)
    size = width * 3.2
    left = (
        x2 - size * math.cos(angle - 0.45),
        y2 - size * math.sin(angle - 0.45),
    )
    right = (
        x2 - size * math.cos(angle + 0.45),
        y2 - size * math.sin(angle + 0.45),
    )
    draw.polygon([end, left, right], fill=fill)


def draw_physics_diagram(draw, scene, font, theme, reveal_ratio=1.0):
    diagram = scene.get("diagram")
    if not isinstance(diagram, dict) or not diagram:
        return False
    diagram_type = str(diagram.get("type") or "force").lower()
    labels = diagram.get("labels") if isinstance(diagram.get("labels"), dict) else {}
    box = (840, 185, 1192, 620)
    draw.rounded_rectangle(box, radius=10, outline=theme["border"], width=2, fill=theme["formula_bg"])
    label_font = font("arialbd.ttf", 18)
    small_font = font("arial.ttf", 15)

    def text(name, fallback):
        return str(labels.get(name) or fallback)

    if diagram_type == "circuit":
        draw.rounded_rectangle((880, 245, 1152, 500), radius=14, outline=theme["primary"], width=5)
        draw.line((910, 325, 910, 425), fill=theme["primary"], width=5)
        draw.line((930, 300, 930, 450), fill=theme["primary"], width=5)
        zigzag = [(980, 245), (995, 275), (1010, 215), (1025, 275), (1040, 215), (1055, 275), (1070, 245)]
        draw.line(zigzag, fill=theme["accent"], width=5, joint="curve")
        draw.ellipse((1080, 455, 1140, 515), outline=theme["primary"], width=5, fill=theme["accent_light"])
        draw.text((1100, 475), "A", font=label_font, fill=theme["primary"])
        draw.text((890, 470), text("U", "U"), font=small_font, fill=theme["text"])
        draw.text((990, 290), text("R", "R"), font=small_font, fill=theme["text"])
        draw.text((1110, 420), text("I", "I"), font=small_font, fill=theme["text"])
        return True

    if diagram_type == "optics":
        draw.line((875, 402, 1160, 402), fill=theme["muted"], width=2)
        draw.ellipse((997, 238, 1047, 566), outline=theme["primary"], width=5, fill=theme["accent_light"])
        draw_arrow(draw, (884, 315), (1022, 402), "#EF4444", width=5)
        draw_arrow(draw, (1022, 402), (1150, 315), "#EF4444", width=5)
        draw_arrow(draw, (884, 490), (1022, 402), theme["accent"], width=5)
        draw_arrow(draw, (1022, 402), (1150, 490), theme["accent"], width=5)
        draw.text((1007, 220), "L", font=label_font, fill=theme["primary"])
        return True

    if diagram_type == "wave":
        draw.line((875, 402, 1160, 402), fill=theme["muted"], width=2)
        points = []
        for x in range(875, 1161, 8):
            y = 402 - math.sin((x - 875) / 285 * math.pi * 4) * 72
            points.append((x, y))
        draw.line(points, fill=theme["accent"], width=6, joint="curve")
        draw.line((1000, 402, 1000, 330), fill="#EF4444", width=3)
        draw.text((1008, 356), "A", font=label_font, fill="#EF4444")
        draw.text((1018, 575), "λ", font=label_font, fill=theme["primary"])
        return True

    if diagram_type == "heat":
        draw.rounded_rectangle((932, 265, 1100, 480), radius=14, outline=theme["primary"], width=5, fill=theme["accent_light"])
        draw.arc((922, 450, 1110, 535), start=190, end=350, fill=theme["accent"], width=6)
        for x in (970, 1018, 1066):
            draw.arc((x - 16, 210, x + 16, 290), start=250, end=110, fill="#EF4444", width=5)
        draw.text((958, 368), "Q = mcΔt", font=label_font, fill=theme["text"])
        return True

    draw.line((875, 520, 1160, 520), fill=theme["muted"], width=4)
    draw.rounded_rectangle((960, 390, 1070, 465), radius=9, outline=theme["primary"], width=5, fill=theme["accent_light"])
    draw.text((984, 420), text("m", "m"), font=label_font, fill=theme["text"])
    draw_arrow(draw, (1070, 428), (1150, 428), "#EF4444", width=6)
    draw.text((1092, 396), text("F", "F"), font=label_font, fill="#EF4444")
    draw_arrow(draw, (1015, 390), (1015, 305), theme["accent"], width=5)
    draw.text((1028, 328), "N", font=label_font, fill=theme["accent"])
    draw_arrow(draw, (1015, 465), (1015, 560), theme["primary"], width=5)
    draw.text((1028, 535), "P", font=label_font, fill=theme["primary"])
    return True


def draw_history_visual(draw, scene, font, theme, reveal_ratio=1.0):
    visual = scene.get("visual")
    if not isinstance(visual, dict) or not visual:
        return False

    visual_type = str(visual.get("type") or "memory_summary").lower()
    box = (840, 185, 1192, 620)
    draw.rounded_rectangle(box, radius=12, outline=theme["border"], width=2, fill=theme["formula_bg"])
    title_font = font("arialbd.ttf", 22)
    label_font = font("arialbd.ttf", 18)
    body_font = font("arial.ttf", 15)

    def draw_small_text(text, xy, max_width=280, max_lines=2, fill=None, line_gap=4):
        lines = wrap_text(draw, str(text or ""), body_font, max_width)[:max_lines]
        draw_multiline(draw, xy, lines, body_font, fill or theme["text"], line_gap)

    def visible(items):
        count = max(1, min(len(items), math.ceil(len(items) * max(0.08, reveal_ratio))))
        return items[:count]

    if visual_type == "timeline":
        events = visual_items(visual, ("events", "items", "nodes")) or []
        events = visible(events[:5] or [{"date": "1", "label": "Boi canh"}, {"date": "2", "label": "Su kien"}, {"date": "3", "label": "Ket qua"}])
        start_y = 242
        gap = 310 / max(len(events) - 1, 1)
        x = 895
        draw.line((x, start_y, x, start_y + gap * (len(events) - 1)), fill=theme["primary"], width=5)
        for idx, event in enumerate(events):
            y = start_y + idx * gap
            draw.ellipse((x - 14, y - 14, x + 14, y + 14), fill=theme["accent"], outline=theme["primary"], width=3)
            date = item_label(event, "date", "year", "time", fallback=f"Moc {idx + 1}")
            label = item_label(event, "label", "text", "title", fallback="Su kien")
            draw.rounded_rectangle((930, y - 30, 1160, y + 36), radius=8, fill=theme["card"], outline=theme["border"], width=1)
            draw.text((946, y - 24), date[:18], font=label_font, fill=theme["accent"])
            draw_small_text(label, (946, y - 2), max_width=196, max_lines=2)
        return True

    if visual_type in {"cause_event_result", "system_diagram"}:
        nodes = visible((visual_items(visual, ("nodes", "items", "events")) or ["Nguyen nhan", "Dien bien", "Ket qua", "Y nghia"])[:4])
        for idx, node in enumerate(nodes):
            y = 220 + idx * 86
            draw.rounded_rectangle((878, y, 1154, y + 58), radius=10, fill=theme["card"], outline=theme["border"], width=2)
            label = item_label(node, "label", "title", fallback=f"Y {idx + 1}")
            body = item_label(node, "text", "description", "value", fallback=str(node))
            draw.text((896, y + 8), label[:24], font=label_font, fill=theme["accent"])
            draw_small_text(body, (896, y + 31), max_width=235, max_lines=1)
            if idx < len(nodes) - 1:
                draw_arrow(draw, (1016, y + 60), (1016, y + 78), theme["primary"], width=3)
        return True

    if visual_type == "compare_board":
        columns = visual.get("columns") if isinstance(visual.get("columns"), list) else []
        if len(columns) < 2:
            columns = [{"title": "Nhom 1", "items": ["Boi canh", "Van de"]}, {"title": "Nhom 2", "items": ["Ket qua", "Y nghia"]}]
        for idx, col in enumerate(columns[:2]):
            x = 868 + idx * 156
            header = (x, 218, x + 136, 262)
            body = (x, 262, x + 136, 580)
            draw.rounded_rectangle((x, 218, x + 136, 580), radius=10, fill=theme["card"], outline=theme["border"], width=2)
            draw.rectangle(header, fill=theme["primary"] if idx == 0 else theme["accent"])
            draw.text((x + 12, 230), item_label(col, "title", "label", fallback=f"Nhom {idx + 1}")[:16], font=label_font, fill="#FFFFFF")
            items = col.get("items") if isinstance(col, dict) and isinstance(col.get("items"), list) else []
            for item_index, item in enumerate(visible(items[:4] or ["Y chinh"])):
                draw_small_text(f"- {item}", (x + 12, 286 + item_index * 62), max_width=112, max_lines=2)
        return True

    if visual_type in {"character_card", "person"}:
        name = str(visual.get("name") or visual.get("title") or "Nhan vat")
        draw.ellipse((968, 218, 1064, 314), fill=theme["accent_light"], outline=theme["accent"], width=4)
        initials = "".join(part[:1] for part in re.findall(r"\w+", name, flags=re.UNICODE)[:2]).upper() or "LS"
        draw.text((996, 248), initials[:3], font=font("arialbd.ttf", 26), fill=theme["primary"])
        title_lines = wrap_text(draw, name, title_font, 260)[:2]
        draw_multiline(draw, (884, 334), title_lines, title_font, theme["primary"], 4)
        items = visible((visual_items(visual) or ["Vai tro", "Dong gop"])[:4])
        for idx, item in enumerate(items):
            draw_small_text(f"- {item_label(item, 'text', 'label', 'title', fallback=str(item))}", (884, 405 + idx * 45), max_width=270, max_lines=2)
        return True

    title = str(visual.get("title") or "Can nho")
    draw.text((878, 218), title[:28], font=title_font, fill=theme["primary"])
    items = visible((visual_items(visual) or ["Moc thoi gian", "Boi canh", "Dien bien", "Ket qua", "Y nghia"])[:6])
    for idx, item in enumerate(items):
        y = 278 + idx * 48
        draw.ellipse((880, y, 906, y + 26), fill=theme["accent"])
        draw.text((888, y + 3), str(idx + 1), font=font("arialbd.ttf", 15), fill="#FFFFFF")
        draw_small_text(item_label(item, "text", "label", "title", fallback=str(item)), (918, y - 2), max_width=230, max_lines=2)
    return True


def draw_geometry(draw, scene, font, theme, reveal_ratio=1.0):
    geometry = scene.get("geometry") or {}
    points = coerce_points(geometry.get("points", {}))
    box = (840, 185, 1192, 620)
    if geometry.get("type") == "circle_diameter_tangent":
        if draw_circle_diameter_geometry(draw, geometry, font, theme, box, reveal_ratio):
            return

    if not points:
        draw.rounded_rectangle(box, radius=10, outline=theme["border"], width=2, fill=theme["formula_bg"])
        draw.text((928, 386), "Hình minh họa", font=font("arialbd.ttf", 24), fill=theme["muted"])
        return

    draw.rounded_rectangle(box, radius=10, outline=theme["border"], width=2, fill=theme["formula_bg"])
    xs = [point[0] for point in points.values()]
    ys = [point[1] for point in points.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)
    pad_x = max(1, span_x * 0.28)
    pad_y = max(1, span_y * 0.28)
    min_x -= pad_x
    max_x += pad_x
    min_y -= pad_y
    max_y += pad_y
    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)

    def to_px(x, y):
        px = box[0] + 26 + (x - min_x) / span_x * (box[2] - box[0] - 52)
        py = box[3] - 26 - (y - min_y) / span_y * (box[3] - box[1] - 52)
        return px, py

    axis_color = theme["muted"]
    if min_x <= 0 <= max_x:
        x0, _ = to_px(0, min_y)
        draw.line((x0, box[1] + 18, x0, box[3] - 18), fill=axis_color, width=1)
        draw.text((x0 + 4, box[1] + 20), "y", font=font("arial.ttf", 14), fill=axis_color)
    if min_y <= 0 <= max_y:
        _, y0 = to_px(min_x, 0)
        draw.line((box[0] + 18, y0, box[2] - 18, y0), fill=axis_color, width=1)
        draw.text((box[2] - 32, y0 + 4), "x", font=font("arial.ttf", 14), fill=axis_color)

    coords = []
    for name, (x, y) in points.items():
        px, py = to_px(x, y)
        coords.append((name, px, py))

    if len(coords) >= 2:
        line_count = max(1, min(len(coords), round(len(coords) * reveal_ratio)))
        visible = coords[:line_count]
        if len(visible) >= 2:
            path = [(x, y) for _, x, y in visible]
            if reveal_ratio >= 0.92 and len(coords) >= 3:
                path.append((coords[0][1], coords[0][2]))
            draw.line(path, fill=theme["primary"], width=4, joint="curve")

    for name, x, y in coords:
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=theme["accent"], outline=theme["primary"], width=3)
        draw.text((x + 12, y - 24), name, font=font("arialbd.ttf", 20), fill=theme["text"])


def draw_scene_visual(draw, scene, font, theme, reveal_ratio=1.0):
    if draw_history_visual(draw, scene, font, theme, reveal_ratio):
        return
    if draw_physics_diagram(draw, scene, font, theme, reveal_ratio):
        return
    draw_geometry(draw, scene, font, theme, reveal_ratio)


def render_history_scene_frame(scene, index, output_path, reveal_ratio=1.0, template_id="history_archive"):
    theme = get_design_template(template_id)
    image = Image.new("RGB", VIDEO_SIZE, theme["bg"])
    draw = ImageDraw.Draw(image)
    font = font_loader()

    draw.rectangle((34, 34, 1246, 686), fill=theme["card"], outline=theme["primary"], width=4)
    for x in range(64, 1220, 42):
        draw.line((x, 48, x, 672), fill=theme["formula_bg"], width=1)
    for y in range(62, 660, 9):
        draw.line((52, y, 1228, y), fill=theme["formula_bg"], width=1)

    section_label = str(scene.get("section_label") or f"PHẦN {index + 1:02d}").upper()
    draw.text((72, 70), section_label, font=font("arialbd.ttf", 23), fill=theme["accent"])
    draw.text((900, 72), "LESSON LOOM HISTORY", font=font("arialbd.ttf", 18), fill=theme["muted"])
    draw.line((72, 110, 1208, 110), fill=theme["primary"], width=4)

    full_title = str(scene.get("title") or "")
    full_narration = scene_display_text(scene)
    narration = reveal_by_units(split_reveal_units(full_narration), reveal_ratio)

    title_font, _, title_spacing = fit_wrapped_text(draw, full_title, "arialbd.ttf", 36, 24, 585, 86, spacing=3)
    draw_multiline(draw, (72, 138), wrap_text(draw, full_title, title_font, 585), title_font, theme["primary"], title_spacing)

    copy_box = (72, 250, 654, 630)
    draw.rectangle(copy_box, fill=theme["card"], outline=theme["border"], width=2)
    draw.rectangle((copy_box[0], copy_box[1], copy_box[0] + 9, copy_box[3]), fill=theme["accent"])
    copy_font, _, copy_spacing = fit_wrapped_text(draw, full_narration, "arial.ttf", 24, 15, 526, 342, spacing=7)
    draw_multiline(draw, (96, 274), wrap_text(draw, narration, copy_font, 526), copy_font, theme["text"], copy_spacing)

    image_ref = str(scene.get("image_ref") or "").replace("\\", "/").strip()
    caption = str(scene.get("image_caption") or "Ảnh minh họa lịch sử")
    photo_box = (676, 138, 1168, 356)
    draw.rectangle(photo_box, fill=theme["formula_bg"], outline=theme["primary"], width=3)
    image_path = output_path.parent / image_ref if image_ref else None
    if image_path and image_path.exists():
        try:
            with Image.open(image_path) as source:
                fitted = ImageOps.fit(source.convert("RGB"), (464, 152), method=Image.Resampling.LANCZOS)
                image.paste(fitted, (690, 152))
        except Exception:
            draw.text((858, 218), "TƯ LIỆU", font=font("arialbd.ttf", 30), fill=theme["muted"])
    else:
        draw.text((858, 218), "TƯ LIỆU", font=font("arialbd.ttf", 30), fill=theme["muted"])
    caption_font = font("arialbd.ttf", 15)
    draw_multiline(draw, (690, 312), wrap_text(draw, caption, caption_font, 454)[:2], caption_font, theme["muted"], 4)

    diagram_box = (676, 374, 1168, 630)
    draw.rectangle(diagram_box, fill=theme["formula_bg"], outline=theme["border"], width=2)
    visual = scene.get("visual") if isinstance(scene.get("visual"), dict) else {}
    visual_title = str(visual.get("title") or "Sơ đồ ghi nhớ")
    draw.text((704, 394), visual_title[:34], font=font("arialbd.ttf", 21), fill=theme["primary"])
    rows, scene_is_summary = history_visual_rows(visual, scene)
    if not rows:
        rows = [("1", "Bối cảnh"), ("2", "Diễn biến"), ("3", "Kết quả"), ("4", "Ý nghĩa")]
    visible_count = max(1, min(len(rows), math.ceil(len(rows) * max(0.1, reveal_ratio))))
    for item_index, (label, body) in enumerate(rows[:visible_count][:3 if scene_is_summary else 4]):
        y = 430 + item_index * 50
        draw.rounded_rectangle((704, y, 1136, y + 38), radius=8, fill=theme["accent_light"], outline=theme["border"], width=1)
        draw.ellipse((718, y + 7, 746, y + 35), fill=theme["accent"])
        draw.text((727, y + 10), str(item_index + 1), font=font("arialbd.ttf", 15), fill="#FFFFFF")
        line = f"{compact_history_visual_text(label, 22)} {compact_history_visual_text(body, 78)}".strip()
        draw_multiline(draw, (760, y + 6), wrap_text(draw, line, font("arialbd.ttf", 14), 352)[:2], font("arialbd.ttf", 14), theme["text"], 3)

    draw.line((72, 650, 1208, 650), fill=theme["border"], width=2)
    draw.text((72, 660), "Tư liệu học tập", font=font("arialbd.ttf", 16), fill=theme["accent"])
    draw.text((1032, 660), "Video lịch sử", font=font("arialbd.ttf", 16), fill=theme["muted"])

    image.save(output_path, "JPEG" if str(output_path).lower().endswith((".jpg", ".jpeg")) else "PNG", quality=88)


def render_scene_frame(scene, index, output_path, reveal_ratio=1.0, template_id="studio"):
    if scene.get('diagram'):
        raise RuntimeError('Slide có sơ đồ Vật lí cần trình dựng HTML để giữ đúng hình học và ký hiệu.')
    if str(template_id or "").startswith("history_") or is_history_subject(scene.get("subject")) or scene.get("image_ref"):
        render_history_scene_frame(scene, index, output_path, reveal_ratio=reveal_ratio, template_id=template_id)
        return
    theme = get_design_template(template_id)
    image = Image.new("RGB", VIDEO_SIZE, theme["bg"])
    draw = ImageDraw.Draw(image)
    font = font_loader()

    draw.rounded_rectangle((40, 40, 1240, 680), radius=16, fill=theme["card"], outline=theme["border"], width=3)
    draw.ellipse((1040, 50, 1220, 230), fill=theme["accent_light"])
    draw.text((80, 75), f"BƯỚC {index + 1:02d}", font=font("arialbd.ttf", 22), fill=theme["accent"])

    full_title = str(scene.get("title") or "")
    full_narration = scene_display_text(scene)
    full_formula_lines = formula_lines(scene.get("latex") or "")
    narration_units = split_reveal_units(full_narration)
    title = full_title if reveal_ratio > 0.02 else ""
    narration = reveal_by_units(narration_units, reveal_ratio)
    visible_formula_lines = reveal_formula_lines(full_formula_lines, reveal_ratio)

    title_font, title_lines, title_spacing = fit_wrapped_text(
        draw, full_title, "arialbd.ttf", 38, 24, 700, 88, spacing=5
    )
    visible_title_lines = wrap_text(draw, title, title_font, 700)
    draw_multiline(draw, (80, 122), visible_title_lines, title_font, theme["primary"], title_spacing)

    narration_box_height = 360 if not full_formula_lines else 190
    narration_font, _, narration_spacing = fit_wrapped_text(
        draw, full_narration, "arial.ttf", 24, 13, 730, narration_box_height, spacing=7
    )
    narration_lines = wrap_text(draw, narration, narration_font, 730)
    draw_multiline(draw, (80, 218), narration_lines, narration_font, theme["text"], narration_spacing)

    if visible_formula_lines:
        formula_box = (72, 430, 820, 650)
        formula_font, rendered_lines, formula_spacing = fit_formula_text(
            draw, visible_formula_lines, "arialbd.ttf", 28, 14, 710, 178, spacing=5
        )
        draw.rounded_rectangle(formula_box, radius=8, fill=theme["formula_bg"])
        draw.rectangle((formula_box[0], formula_box[1], formula_box[0] + 6, formula_box[3]), fill=theme["accent"])
        draw_multiline(draw, (92, 452), rendered_lines, formula_font, theme["primary"], formula_spacing)

    draw_scene_visual(draw, scene, font, theme, reveal_ratio)

    image.save(output_path, "JPEG" if str(output_path).lower().endswith((".jpg", ".jpeg")) else "PNG", quality=88)


def render_scene_png(scene, index, output_path, template_id="studio"):
    render_scene_frame(scene, index, output_path, reveal_ratio=1.0, template_id=template_id)


def ensure_scene_png(scene, index, html_path, png_path, template_id="studio"):
    if png_path.exists() and png_path.stat().st_size > 0:
        return True
    rendered_with_browser = render_scene_png_with_playwright(html_path, png_path)
    if not rendered_with_browser:
        render_scene_png(scene, index, png_path, template_id=template_id)
    return png_path.exists() and png_path.stat().st_size > 0


def scene_motion_filter(index, duration):
    fade_out_start = max(float(duration) - 0.45, 0)
    phase = index * 0.85
    return (
        "zoompan="
        "z='min(1+0.0009*on,1.075)':"
        f"x='iw/2-(iw/zoom/2)+sin(on/36+{phase:.2f})*18':"
        f"y='ih/2-(ih/zoom/2)+cos(on/42+{phase:.2f})*10':"
        "d=1:s=1280x720:fps=25,"
        "eq=saturation=1.04:contrast=1.015,"
        "fade=t=in:st=0:d=0.35,"
        f"fade=t=out:st={fade_out_start:.3f}:d=0.45,"
        "format=yuv420p"
    )


def render_scene_video(ffmpeg_bin, png_path, mp3_path, output_path, duration, index, has_audio):
    motion_filter = scene_motion_filter(index, duration)
    cmd = [
        ffmpeg_bin, "-y",
        "-loop", "1", "-framerate", "25",
        "-i", str(png_path),
    ]
    if has_audio:
        cmd.extend(["-i", str(mp3_path)])
    cmd.extend([
        "-t", f"{duration:.3f}",
        "-vf", motion_filter,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
    ])
    if has_audio:
        cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])
    else:
        cmd.append("-an")
    cmd.extend(["-movflags", "+faststart", str(output_path)])

    cmd[-1:-1] = ['-threads', '1']
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=900)
    if result.returncode == 0 and output_path.exists():
        return True

    print(f"Motion render failed for {output_path.name}: {(result.stderr or '')[-800:]}")
    fallback_filter = f"fade=t=in:st=0:d=0.25,fade=t=out:st={max(float(duration) - 0.35, 0):.3f}:d=0.35,format=yuv420p"
    fallback = [
        ffmpeg_bin, "-y",
        "-loop", "1", "-framerate", "25",
        "-i", str(png_path),
    ]
    if has_audio:
        fallback.extend(["-i", str(mp3_path)])
    fallback.extend([
        "-t", f"{duration:.3f}",
        "-vf", fallback_filter,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
    ])
    if has_audio:
        fallback.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])
    else:
        fallback.append("-an")
    fallback.append(str(output_path))
    fallback[-1:-1] = ['-threads', '1']
    subprocess.run(fallback, capture_output=True, check=False, timeout=900)
    return output_path.exists()


def reveal_latex_lines_for_html(value, reveal_ratio):
    text = normalize_latex_input(value) or ""
    if "\\begin{cases}" in text or "\\begin{aligned}" in text or "\\begin{gathered}" in text:
        return latex_for_katex(text)
    lines = split_latex_display_lines(value)
    if not lines:
        return ""
    visible_count = max(1, min(len(lines), int(len(lines) * reveal_ratio + 0.999)))
    return latex_for_katex(r" \\ ".join(lines[:visible_count]))


def render_typewriter_frames_with_playwright(html_path, scene, index, frame_dir, frame_count, text_done_frame):
    if importlib.util.find_spec("playwright") is None:
        return False
    try:
        from playwright.sync_api import sync_playwright

        is_full_solution = str(scene.get("layout") or "") == "full_solution"
        narration_units = split_reveal_units(scene_display_text(scene))
        full_latex = str(scene.get("latex") or "")
        width, height = VIDEO_SIZE
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel=os.getenv("PLAYWRIGHT_CHANNEL") or None)
            try:
                page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                page.goto(html_path.resolve().as_uri(), wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1200)
                page.evaluate('document.fonts.ready')
                check_slide_layout(page)
                for frame_index in range(frame_count):
                    if frame_index >= text_done_frame:
                        reveal = 1.0
                    else:
                        reveal = frame_index / text_done_frame
                    payload = {
                        "reveal": reveal,
                        "narration": reveal_by_units(narration_units, reveal),
                        "latex": reveal_latex_lines_for_html(full_latex, reveal),
                        "keepMarkup": is_full_solution,
                    }
                    page.evaluate(
                        """(payload) => {
                          const narration = document.querySelector('.narration, .history-copy');
                          const formula = document.querySelector('.formula');
                          document.querySelectorAll('.fit-text, .formula').forEach((node) => {
                            node.style.fontSize = '';
                          });
                          if (narration && !payload.keepMarkup) {
                            const units = narration.querySelectorAll('.slide-unit');
                            if (units.length) {
                              const count = Math.ceil(payload.reveal * units.length);
                              units.forEach((node, i) => node.style.visibility = i < count ? 'visible' : 'hidden');
                            } else narration.textContent = payload.narration || ' ';
                          }
                          if (formula) {
                            formula.dataset.latex = payload.latex || '';
                            if (typeof window.renderFormula === 'function') window.renderFormula();
                          }
                          if (typeof window.fitText === 'function') window.fitText();
                        }""",
                        payload,
                    )
                    frame_path = frame_dir / f"frame-{frame_index + 1:04d}.jpg"
                    page.screenshot(path=str(frame_path), type="jpeg", quality=88)
            finally:
                browser.close()
        return bool(list(frame_dir.glob("frame-*.jpg")))
    except Exception as e:
        print(f"HTML typewriter render fallback for scene {index + 1}: {e}")
        return False


def render_scene_video_typewriter(ffmpeg_bin, scene, index, frame_dir, mp3_path, output_path, duration, has_audio, template_id="studio", html_path=None):
    target_fps = env_int("RENDER_FRAME_FPS", 5, 2, 12)
    html_frames_enabled = os.getenv("RENDER_HTML_TYPEWRITER", "1").strip().lower() not in {"0", "false", "off", "no"}
    max_frames = env_int("RENDER_MAX_FRAMES", 90, 24, 180)
    if html_frames_enabled:
        max_frames = max(24, min(max_frames, env_int("RENDER_HTML_MAX_FRAMES", 36, 24, 180)))
    frame_count = max(24, min(max_frames, int(float(duration) * target_fps) + 1))
    source_fps = max(0.05, frame_count / max(float(duration), 0.1))
    text_done_frame = max(1, int(frame_count * 0.78))

    if frame_dir.exists():
        shutil.rmtree(frame_dir, ignore_errors=True)
    frame_dir.mkdir(parents=True, exist_ok=True)

    rendered_frames = False
    if html_frames_enabled and html_path:
        rendered_frames = render_typewriter_frames_with_playwright(
            html_path,
            scene,
            index,
            frame_dir,
            frame_count,
            text_done_frame,
        )

    if not rendered_frames:
        if html_frames_enabled:
            raise RuntimeError('Trình dựng HTML/Chromium chưa sẵn sàng. Dừng để tránh video sai bố cục hoặc sơ đồ.')
        shutil.rmtree(frame_dir, ignore_errors=True)
        frame_dir.mkdir(parents=True, exist_ok=True)
        for frame_index in range(frame_count):
            if frame_index >= text_done_frame:
                reveal = 1.0
            else:
                reveal = frame_index / text_done_frame
            frame_path = frame_dir / f"frame-{frame_index + 1:04d}.jpg"
            render_scene_frame(scene, index, frame_path, reveal_ratio=reveal, template_id=template_id)

    input_pattern = frame_dir / "frame-%04d.jpg"
    fade_out_start = max(float(duration) - 0.45, 0)
    vf = (
        "scale=1280:720,"
        "eq=saturation=1.04:contrast=1.015,"
        "fade=t=in:st=0:d=0.25,"
        f"fade=t=out:st={fade_out_start:.3f}:d=0.45,"
        "format=yuv420p"
    )
    cmd = [
        ffmpeg_bin,
        "-y",
        "-framerate",
        f"{source_fps:.3f}",
        "-i",
        str(input_pattern),
    ]
    if has_audio:
        cmd.extend(["-i", str(mp3_path)])
    cmd.extend([
        "-t",
        f"{duration:.3f}",
        "-vf",
        vf,
        "-r",
        "25",
        "-fps_mode",
        "cfr",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
    ])
    if has_audio:
        cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])
    else:
        cmd.append("-an")
    cmd.extend(["-movflags", "+faststart", str(output_path)])

    cmd[-1:-1] = ['-threads', '1']
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=900)
    ok = result.returncode == 0 and output_path.exists()
    if not ok:
        print(f"Typewriter render failed for {output_path.name}: {(result.stderr or '')[-800:]}")
    shutil.rmtree(frame_dir, ignore_errors=True)
    return ok


def render_scene_asset(job_dir, scene, index, template_id, ffmpeg_bin):
    html_path = job_dir / f"scene-{index + 1}.html"
    svg_path = job_dir / f"scene-{index + 1}.svg"
    png_path = job_dir / f"scene-{index + 1}.png"
    mp3_path = job_dir / f"scene-{index + 1}.mp3"
    scene_mp4_path = job_dir / f"scene-{index + 1}.mp4"

    render_scene_html(scene, index, html_path, template_id=template_id)
    svg_path.write_text(scene_svg(scene, index), encoding="utf-8")

    tts_ok, tts_source = generate_tts(narration_speech_text(scene.get("narration", "")), mp3_path)
    scene_duration = media_duration_seconds(mp3_path) if tts_ok else None
    if not scene_duration:
        raise RuntimeError(f"Scene {index + 1}: không tạo được âm thanh hợp lệ; dừng để tránh video mất tiếng.")
    scene["duration_seconds"] = round(scene_duration, 2)

    has_audio = tts_ok and mp3_path.exists()
    rendered_scene = False
    if ffmpeg_bin:
        frame_dir = job_dir / f"frames-scene-{index + 1}"
        rendered_scene = render_scene_video_typewriter(
            ffmpeg_bin,
            scene,
            index,
            frame_dir,
            mp3_path,
            scene_mp4_path,
            scene_duration,
            has_audio,
            template_id,
            html_path,
        )
        if not rendered_scene and ensure_scene_png(scene, index, html_path, png_path, template_id=template_id):
            rendered_scene = render_scene_video(
                ffmpeg_bin,
                png_path,
                mp3_path,
                scene_mp4_path,
                scene_duration,
                index,
                has_audio,
            )
    else:
        ensure_scene_png(scene, index, html_path, png_path, template_id=template_id)

    mp3_info = probe_media_info(mp3_path) if mp3_path.exists() else {}
    mp4_info = probe_media_info(scene_mp4_path) if rendered_scene else {}
    return {
        "index": index,
        "scene": scene,
        "mp4_path": scene_mp4_path if rendered_scene else None,
        "mp3_path": mp3_path if mp3_path.exists() else None,
        "duration": scene_duration,
        "has_audio": has_audio,
        "tts_source": tts_source,
        "mp3_duration": mp3_info.get("duration"),
        "mp4_duration": mp4_info.get("duration"),
        "mp4_video_duration": mp4_info.get("video_duration"),
        "mp4_audio_duration": mp4_info.get("audio_duration"),
    }


def render_job(job_id, script=None):
    if not is_valid_job_id(job_id):
        raise ValueError("job_id không hợp lệ.")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("Cần cài ffmpeg và ffprobe vào PATH trước khi render video.")
    with jobs_lock:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 5
        jobs[job_id]["render_note"] = "Bắt đầu tạo kịch bản, âm thanh và các slide..."

    job_dir = MEDIA_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    if not script:
        script_file = job_dir / "script.json"
        if script_file.exists():
            script = json.loads(script_file.read_text(encoding="utf-8"))
        else:
            raise ValueError("Không tìm thấy kịch bản để render.")

    script = sanitize_script_for_render(
        script,
        original_problem=str((script or {}).get("problem") or ""),
        subject=(script or {}).get("subject"),
    )
    script = apply_history_assets(script, script.get("history_assets") or [])
    (job_dir / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    template_id = script.get("design_template") or script.get("theme") or "studio"
    if template_id not in DESIGN_TEMPLATES:
        template_id = "studio"
    script["design_template"] = template_id
    scenes = expand_long_scenes(script.get("steps", []))
    if not scenes:
        raise ValueError("Kịch bản không có cảnh để render.")
    script["steps"] = scenes
    total_scenes = max(len(scenes), 1)

    scene_mp4_files = []
    ffmpeg_bin = shutil.which("ffmpeg")
    render_log = {
        "job_id": job_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scenes": [],
        "warnings": [],
        "final": {},
    }
    render_warnings = []

    max_workers = min(env_int("RENDER_WORKERS", 3, 1, 8), total_scenes)
    completed = 0
    scene_results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(render_scene_asset, job_dir, scene, index, template_id, ffmpeg_bin): index
            for index, scene in enumerate(scenes)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                result = future.result()
                scene_results[index] = result
                scenes[index] = result["scene"]
                if result["mp4_path"]:
                    scene_mp4_files.append(result["mp4_path"])
                scene_log = {
                    "index": index + 1,
                    "title": result["scene"].get("title"),
                    "expected_duration": round(float(result.get("duration") or 0), 3),
                    "mp3": Path(result["mp3_path"]).name if result.get("mp3_path") else None,
                    "mp3_duration": result.get("mp3_duration"),
                    "mp4": Path(result["mp4_path"]).name if result.get("mp4_path") else None,
                    "mp4_duration": result.get("mp4_duration"),
                    "mp4_video_duration": result.get("mp4_video_duration"),
                    "mp4_audio_duration": result.get("mp4_audio_duration"),
                    "has_audio": result.get("has_audio"),
                    "tts_source": result.get("tts_source"),
                }
                render_log["scenes"].append(scene_log)
                scene_video = scene_log.get("mp4_video_duration") or scene_log.get("mp4_duration")
                scene_audio = scene_log.get("mp4_audio_duration")
                if scene_log.get("has_audio") and (not scene_audio or not scene_video):
                    render_warnings.append(f"Scene {index + 1} thiếu audio/video sau khi render.")
                elif scene_video and scene_audio and abs(scene_video - scene_audio) > max(1.5, scene_video * 0.05):
                    render_warnings.append(
                        f"Scene {index + 1} lệch audio {scene_audio:.1f}s / video {scene_video:.1f}s."
                    )
                audio_note = "audio cache" if result.get("tts_source") == "cache" else "audio mới"
                note = f"Đã dựng chữ động scene {index + 1}/{total_scenes} ({result['duration']:.1f}s, {audio_note})"
            except Exception as e:
                note = f"Lỗi khi dựng scene {index + 1}/{total_scenes}: {e}"
                render_warnings.append(note)
                render_log["scenes"].append({
                    "index": index + 1,
                    "error": str(e),
                })
                print(note)
            completed += 1
            progress_pct = 10 + round((completed / total_scenes) * 75)
            with jobs_lock:
                jobs[job_id]["progress"] = progress_pct
                jobs[job_id]["render_note"] = f"{note} · worker {max_workers} luồng"

    scene_mp4_files = [
        scene_results[index]["mp4_path"]
        for index in sorted(scene_results)
        if scene_results[index].get("mp4_path")
    ]

    (job_dir / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")

    video_path = job_dir / "result.mp4"

    if len(scene_mp4_files) != len(scenes) or any(
        not result.get("has_audio") or not result.get("mp4_audio_duration")
        for result in scene_results.values()
    ):
        render_log["warnings"] = render_warnings
        (job_dir / "render-log.json").write_text(json.dumps(render_log, ensure_ascii=False, indent=2), encoding="utf-8")
        raise RuntimeError("Có cảnh bị lỗi hoặc thiếu tiếng; không ghép video thiếu nội dung.")

    if ffmpeg_bin and scene_mp4_files:
        concat_result = concat_scene_videos(ffmpeg_bin, job_dir, scene_mp4_files, video_path)
        final_info = probe_media_info(video_path)
        render_log["final"]["concat_copy"] = concat_result
        render_log["final"]["after_copy"] = final_info

        if (not concat_result["ok"]) or is_audio_video_mismatch(final_info) or (
            any(result.get("has_audio") for result in scene_results.values()) and not final_info.get("has_audio")
        ):
            if final_info.get("audio_duration") and final_info.get("video_duration"):
                render_warnings.append(
                    "Final concat bị lệch audio/video, đang tự chuẩn hóa lại từng scene trước khi ghép."
                )
            normalized_files = []
            for source_path in scene_mp4_files:
                normalized_path = source_path.with_name(f"{source_path.stem}.normalized.mp4")
                if normalize_scene_video(ffmpeg_bin, source_path, normalized_path):
                    normalized_files.append(normalized_path)
                else:
                    render_warnings.append(f"Không chuẩn hóa được {source_path.name}.")

            if len(normalized_files) == len(scene_mp4_files):
                fixed_path = job_dir / "result.fixed.mp4"
                fixed_result = concat_scene_videos(
                    ffmpeg_bin,
                    job_dir,
                    normalized_files,
                    fixed_path,
                    suffix="-normalized",
                )
                fixed_info = probe_media_info(fixed_path)
                render_log["final"]["normalized_concat"] = fixed_result
                render_log["final"]["after_normalized"] = fixed_info
                if fixed_result["ok"] and fixed_path.exists():
                    shutil.move(str(fixed_path), video_path)
                    final_info = probe_media_info(video_path)
                for temp_path in normalized_files:
                    try:
                        temp_path.unlink(missing_ok=True)
                    except OSError:
                        pass

        render_log["final"]["result"] = probe_media_info(video_path)

    final_info = probe_media_info(video_path)
    if video_path.exists():
        if not final_info.get("has_audio") and any(result.get("has_audio") for result in scene_results.values()):
            render_warnings.append("Video cuối không có audio dù các scene đã tạo audio.")
        elif is_audio_video_mismatch(final_info):
            video_duration = final_info.get("video_duration") or final_info.get("duration") or 0
            audio_duration = final_info.get("audio_duration") or 0
            render_warnings.append(
                f"Video tạo xong nhưng audio chỉ dài {audio_duration:.1f}s / video {video_duration:.1f}s."
            )

    render_warnings = list(dict.fromkeys(render_warnings))
    render_log["warnings"] = render_warnings
    render_log["final"]["result"] = final_info
    render_log_path = job_dir / "render-log.json"
    render_log_path.write_text(json.dumps(render_log, ensure_ascii=False, indent=2), encoding="utf-8")

    expected_duration = sum(float(result["duration"]) for result in scene_results.values())
    actual_duration = final_info.get("video_duration") or 0
    if (not final_info.get("has_audio") or not actual_duration
            or is_audio_video_mismatch(final_info)
            or abs(actual_duration - expected_duration) > max(2, expected_duration * 0.03)):
        raise RuntimeError("Video cuối không đạt kiểm tra âm thanh/thời lượng; xem render-log.json.")

    if video_path.exists() and render_warnings:
        render_note = render_warnings[-1]
    elif video_path.exists():
        render_note = "Video MP4 lồng tiếng hoàn chỉnh đã được tạo thành công!"
    else:
        render_note = "Đã hoàn thành tạo kịch bản & hình ảnh scene."
    video_duration = final_info.get("video_duration") or final_info.get("duration")
    audio_duration = final_info.get("audio_duration")

    with jobs_lock:
        jobs[job_id].update({
            "status": "complete",
            "progress": 100,
            "scene_count": len(scenes),
            "has_video": video_path.exists(),
            "render_note": render_note,
            "render_warnings": render_warnings,
            "render_log_url": f"/media/{job_id}/render-log.json" if render_log_path.exists() else None,
            "duration_seconds": round(video_duration, 2) if video_duration else None,
            "audio_duration_seconds": round(audio_duration, 2) if audio_duration else None,
        })


def safe_render_job(job_id, script=None):
    try:
        render_job(job_id, script)
    except Exception as error:
        message = f"Lỗi render: {error}"
        print(message)
        with jobs_lock:
            job = jobs.get(job_id)
            if job is not None:
                job.update({
                    "status": "error",
                    "progress": job.get("progress", 0),
                    "has_video": False,
                    "render_note": message,
                    "render_warnings": [message],
                })


def history_item(job_dir):
    if not job_dir.is_dir():
        return None

    script_path = job_dir / "script.json"
    video_path = job_dir / "result.mp4"
    render_log_path = job_dir / "render-log.json"
    if not script_path.exists() and not video_path.exists():
        return None

    script = {}
    if script_path.exists():
        try:
            script = json.loads(script_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"History script read error for {job_dir.name}: {e}")

    problem = str(script.get("problem") or "").strip()
    steps = script.get("steps") if isinstance(script.get("steps"), list) else []
    if not problem and steps:
        problem = str(steps[0].get("title") or "").strip()
    if not problem:
        problem = f"Video {job_dir.name}"

    image_path = next(job_dir.glob("problem-image.*"), None)
    updated_at = max(
        [p.stat().st_mtime for p in job_dir.iterdir() if p.is_file()],
        default=job_dir.stat().st_mtime,
    )
    video_size = video_path.stat().st_size if video_path.exists() else 0
    video_duration = media_duration_seconds(video_path) if video_path.exists() else None
    audio_duration = media_audio_duration_seconds(video_path) if video_path.exists() else None
    render_warnings = []
    if render_log_path.exists():
        try:
            render_log = json.loads(render_log_path.read_text(encoding="utf-8"))
            render_warnings = render_log.get("warnings") or []
        except Exception as e:
            print(f"History render log read error for {job_dir.name}: {e}")
    if video_path.exists():
        media_info = {
            "duration": video_duration,
            "video_duration": video_duration,
            "audio_duration": audio_duration,
            "has_audio": bool(audio_duration),
        }
        if not audio_duration:
            render_warnings.append("Video lịch sử không có audio stream.")
        elif is_audio_video_mismatch(media_info):
            render_warnings.append(
                f"Video lịch sử lệch audio {audio_duration:.1f}s / video {video_duration:.1f}s."
            )
        render_warnings = list(dict.fromkeys(render_warnings))

    with jobs_lock:
        live_job = jobs.get(job_dir.name, {}).copy()

    return {
        "id": job_dir.name,
        "problem": problem,
        "created_at": live_job.get("created_at"),
        "updated_at": datetime.fromtimestamp(updated_at, timezone.utc).isoformat(),
        "status": live_job.get("status") or ("complete" if video_path.exists() else "script_ready"),
        "progress": live_job.get("progress", 100 if video_path.exists() else 0),
        "scene_count": live_job.get("scene_count") or len(steps),
        "has_video": video_path.exists(),
        "video_url": f"/media/{job_dir.name}/result.mp4" if video_path.exists() else None,
        "download_url": f"/media/{job_dir.name}/result.mp4" if video_path.exists() else None,
        "script_url": f"/api/scenes/{job_dir.name}" if script_path.exists() else None,
        "image_url": f"/media/{job_dir.name}/{image_path.name}" if image_path else live_job.get("image_url"),
        "history_assets": script.get("history_assets") or live_job.get("history_assets") or [],
        "video_size": video_size,
        "duration_seconds": round(video_duration, 2) if video_duration else None,
        "audio_duration_seconds": round(audio_duration, 2) if audio_duration else None,
        "render_warnings": live_job.get("render_warnings") or render_warnings,
        "render_log_url": live_job.get("render_log_url") or (f"/media/{job_dir.name}/render-log.json" if render_log_path.exists() else None),
    }
