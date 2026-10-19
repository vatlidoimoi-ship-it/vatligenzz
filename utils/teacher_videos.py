"""Teacher-only video studio, backed by Supabase jobs and private Storage."""
import copy
from datetime import datetime, timezone
from functools import wraps
import hmac
import os
import re
import secrets
import shutil
import threading
import time
import uuid
import tempfile
import io
from pathlib import Path

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for, send_file
from .video_store import VideoStore

ID = re.compile(r'^[0-9a-f]{10}$')
ACTIVE = {'queued_draft', 'drafting', 'queued', 'processing'}
THEMES = {'studio': 'Studio xanh', 'chalkboard': 'Bảng phấn', 'notebook': 'Vở ghi',
          'warm': 'Warm Focus', 'neon': 'Dark Neon'}


def now():
    return datetime.now(timezone.utc).isoformat()


def validated_script(payload, original):
    if not isinstance(payload, dict) or not isinstance(payload.get('steps'), list):
        raise ValueError('Kịch bản phải có danh sách các bước.')
    if not 1 <= len(payload['steps']) <= 24:
        raise ValueError('Mỗi video cần từ 1 đến 24 bước.')
    theme = payload.get('design_template', 'studio')
    if theme not in THEMES:
        raise ValueError('Mẫu thiết kế không hợp lệ.')
    script = {'problem': original.get('problem', ''), 'subject': 'Vật lý',
              'design_template': theme, 'steps': []}
    for index, item in enumerate(payload['steps']):
        if not isinstance(item, dict):
            raise ValueError('Bước giảng không hợp lệ.')
        step = {}
        for field, limit in [('title', 180), ('narration', 2200), ('slide_text', 1400), ('latex', 1400)]:
            value = item.get(field) or ''
            if not isinstance(value, str) or len(value) > limit:
                raise ValueError(f'Nội dung bước {index + 1} quá dài hoặc sai định dạng.')
            step[field] = value.strip()
        if not step['narration']:
            raise ValueError(f'Bước {index + 1} cần lời thuyết minh.')
        # Only preserve server-generated diagrams; never accept local paths or image URLs.
        previous = (original.get('steps') or [])
        if index < len(previous):
            for field in ['geometry', 'diagram', 'layout']:
                if field in previous[index]:
                    step[field] = copy.deepcopy(previous[index][field])
        script['steps'].append(step)
    if sum(len(s['narration']) for s in script['steps']) > 16000:
        raise ValueError('Lời đọc quá dài. Hãy chia thành nhiều video ngắn.')
    return script


def register_teacher_videos(app, get_user, store=None, start_worker=True):
    store = store or VideoStore()
    bp = Blueprint('teacher_videos', __name__, url_prefix='/teacher/videos')
    wake = threading.Event()
    preview_lock = threading.Lock()

    @bp.after_request
    def private_response(response):
        response.headers['Cache-Control'] = 'private, no-store'
        return response

    def protected(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            user_id = session.get('user_id')
            user = get_user(user_id) if user_id else None
            if not user:
                if request.path.endswith('/videos'):
                    return redirect(url_for('login'))
                return jsonify(error='Vui lòng đăng nhập.'), 401
            if user.get('role') not in {'teacher', 'admin'}:
                return jsonify(error='Chỉ giáo viên hoặc quản trị viên được quản lý video.'), 403
            if request.method == 'POST':
                token = request.headers.get('X-CSRF-Token', '')
                if not token or not hmac.compare_digest(token, session.get('video_csrf', '')):
                    return jsonify(error='Phiên làm việc đã đổi. Vui lòng tải lại trang.'), 403
            return function(*args, **kwargs)
        return wrapped

    def own_row(job_id):
        if not ID.fullmatch(job_id):
            return None
        row = store.get(job_id)
        user = get_user(session['user_id'])
        return row if row and (row['value'].get('owner_id') == str(session['user_id']) or user.get('role') == 'admin') else None

    @bp.errorhandler(RuntimeError)
    def storage_error(error):
        app.logger.error('Video storage unavailable: %s', type(error).__name__)
        return jsonify(error='Kho video tạm thời chưa sẵn sàng. Vui lòng thử lại.'), 503

    @bp.get('')
    @protected
    def studio():
        session.setdefault('video_csrf', secrets.token_hex(24))
        return render_template('teacher_videos.html', video_csrf=session['video_csrf'], themes=THEMES)

    @bp.get('/jobs')
    @protected
    def listing():
        user = get_user(session['user_id'])
        rows = store.list(owner=None if user.get('role') == 'admin' else str(session['user_id']))
        return jsonify(items=[public(row['value'], include_script=False) for row in rows])

    @bp.post('/jobs')
    @protected
    def create():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error='Dữ liệu không hợp lệ.'), 400
        problem = data.get('problem', '')
        if not isinstance(problem, str) or not 15 <= len(problem.strip()) <= 12000:
            return jsonify(error='Đề bài cần từ 15 đến 12.000 ký tự.'), 400
        rows = store.list(owner=str(session['user_id']))
        if any(r['value'].get('status') in ACTIVE for r in rows):
            return jsonify(error='Bạn đang có một tác vụ chạy. Hãy chờ hoàn tất.'), 409
        job = {'id': uuid.uuid4().hex[:10], 'owner_id': str(session['user_id']),
               'problem': problem.strip(), 'status': 'queued_draft', 'progress': 0,
               'created_at': now(), 'updated_at': now(), 'note': 'Đang chờ tạo kịch bản.'}
        store.create(job)
        wake.set()
        return jsonify(job=public(job)), 202

    @bp.get('/jobs/<job_id>')
    @protected
    def detail(job_id):
        row = own_row(job_id)
        if not row:
            return jsonify(error='Không tìm thấy video.'), 404
        return jsonify(job=public(row['value']))

    @bp.post('/jobs/<job_id>/render')
    @protected
    def render(job_id):
        row = own_row(job_id)
        if not row:
            return jsonify(error='Không tìm thấy video.'), 404
        job = row['value']
        if job['status'] not in {'script_ready', 'error'} or not job.get('script'):
            return jsonify(error='Tác vụ đang chạy hoặc chưa có kịch bản.'), 409
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            return jsonify(error='Máy chủ chưa cài công cụ dựng video. Vui lòng liên hệ quản trị viên.'), 503
        try:
            script = validated_script(request.get_json(silent=True), job['script'])
        except ValueError as error:
            return jsonify(error=str(error)), 400
        for existing in store.list(owner=job['owner_id']):
            if existing['value']['id'] != job_id and existing['value'].get('status') in ACTIVE:
                return jsonify(error='Bạn đang có tác vụ khác chạy.'), 409
        updated = {**job, 'script': script, 'status': 'queued', 'progress': 0,
                   'note': 'Đang chờ dựng video.', 'updated_at': now()}
        if not store.change(row, updated):
            return jsonify(error='Tác vụ vừa thay đổi. Hãy tải lại.'), 409
        wake.set()
        return jsonify(job=public(updated)), 202

    @bp.post('/jobs/<job_id>/preview')
    @protected
    def preview(job_id):
        row = own_row(job_id)
        if not row or not row['value'].get('script'):
            return jsonify(error='Không tìm thấy kịch bản.'), 404
        payload = request.get_json(silent=True)
        try:
            script = validated_script(payload, row['value']['script'])
            index = payload.get('preview_index', 0)
            if type(index) is not int or not 0 <= index < len(script['steps']):
                raise ValueError('Bước xem trước không hợp lệ.')
        except ValueError as error:
            return jsonify(error=str(error)), 400
        if not preview_lock.acquire(blocking=False):
            return jsonify(error='Đang tạo ảnh xem trước. Vui lòng thử lại sau vài giây.'), 429
        try:
            from botvideo import core
            with tempfile.TemporaryDirectory(prefix='video-preview-') as directory:
                html, png = Path(directory)/'scene.html', Path(directory)/'scene.png'
                core.render_scene_html(script['steps'][index], index, html, script['design_template'])
                if not core.render_scene_png_with_playwright(html, png):
                    return jsonify(error='Chưa tạo được preview. Hãy rút gọn chữ nếu slide dài; nếu vẫn lỗi, máy chủ cần kiểm tra trình dựng Chromium.'), 503
                image = io.BytesIO(png.read_bytes())
            return send_file(image, mimetype='image/png')
        finally:
            preview_lock.release()

    @bp.get('/jobs/<job_id>/play')
    @protected
    def play(job_id):
        row = own_row(job_id)
        if not row or row['value'].get('status') != 'complete' or not row['value'].get('object_key'):
            return jsonify(error='Video chưa sẵn sàng.'), 404
        response = redirect(store.signed_url(row['value']['object_key']))
        response.headers['Cache-Control'] = 'no-store'
        return response

    @bp.post('/jobs/<job_id>/publication')
    @protected
    def publication(job_id):
        row = own_row(job_id)
        if not row:
            return jsonify(error='Không tìm thấy video.'), 404
        job = row['value']
        if job.get('status') != 'complete' or not job.get('object_key'):
            return jsonify(error='Chỉ xuất bản video đã dựng và lưu thành công.'), 409
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or type(payload.get('published')) is not bool:
            return jsonify(error='Trạng thái xuất bản không hợp lệ.'), 400
        metadata = dict(job.get('publication') or {})
        if payload['published']:
            for field, label, limit in [('title', 'Tên bài', 180), ('group', 'Chủ đề', 120), ('description', 'Mô tả', 1500)]:
                value = payload.get(field, '')
                if not isinstance(value, str) or len(value) > limit or (field != 'description' and not value.strip()):
                    return jsonify(error=f'{label} không hợp lệ (tối đa {limit} ký tự).'), 400
                metadata[field] = value.strip()
            if not isinstance(payload.get('grade'), str) or payload['grade'] not in {'10', '11', '12'}:
                return jsonify(error='Chọn lớp 10, 11 hoặc 12.'), 400
            metadata['grade'] = payload['grade']
            metadata.setdefault('published_at', now())
        metadata.update(published=payload['published'], updated_at=now(), updated_by=str(session['user_id']))
        updated = {**job, 'publication': metadata, 'updated_at': now()}
        if not store.change(row, updated):
            return jsonify(error='Video vừa thay đổi. Hãy tải lại trước khi xuất bản.'), 409
        return jsonify(job=public(updated))

    def public(job, include_script=True):
        fields = ['id', 'problem', 'status', 'progress', 'note', 'created_at', 'duration_seconds']
        result = {key: job.get(key) for key in fields}
        result['publication'] = job.get('publication') or {'published': False}
        if result['publication'].get('published'):
            result['lesson_url'] = '/video-lessons/teacher-' + job['id']
        if include_script and job.get('script'):
            result['script'] = job['script']
        if job.get('status') == 'complete':
            result['video_url'] = url_for('teacher_videos.play', job_id=job['id'])
        return result

    def run_one(row):
        job = row['value']
        draft = job['status'] == 'queued_draft'
        claimed = store.change(row, {**job, 'status': 'drafting' if draft else 'processing',
                                    'updated_at': now(), 'note': 'Đang tạo kịch bản.' if draft else 'Đang dựng video.'})
        if not claimed:
            return
        job = claimed['value']
        from botvideo import core
        outcome = {}

        def work():
            try:
                if draft:
                    script = core.ask_gemini(job['problem'], 'Vật lý')
                    # Reject oversized or malformed AI output before teacher preview.
                    script = validated_script(script, script)
                    outcome.update(script=script, status='script_ready', progress=0,
                                   note='Kịch bản sẵn sàng. Hãy kiểm tra nội dung rồi bấm dựng video.')
                else:
                    with core.jobs_lock:
                        core.jobs[job['id']] = {'status': 'queued', 'progress': 0}
                    core.safe_render_job(job['id'], copy.deepcopy(job['script']))
                    with core.jobs_lock:
                        result = dict(core.jobs[job['id']])
                    if result['status'] != 'complete':
                        raise RuntimeError('Render failed')
                    object_key = store.upload(job['id'], core.MEDIA_DIR / job['id'] / 'result.mp4')
                    outcome.update(status='complete', progress=100, object_key=object_key,
                                   duration_seconds=result.get('duration_seconds'), note='Video đã lưu và sẵn sàng phát có tiếng.')
            except Exception:
                app.logger.exception('Teacher video job failed: %s', job['id'])
                outcome.update(status='error', note='Không hoàn tất được tác vụ. Kiểm tra kịch bản và thử lại; nếu vẫn lỗi hãy liên hệ quản trị viên.')

        thread = threading.Thread(target=work, daemon=True)
        thread.start()
        while thread.is_alive():
            thread.join(timeout=5)
            progress = 0
            if not draft:
                with core.jobs_lock:
                    progress = core.jobs.get(job['id'], {}).get('progress', 0)
            refreshed = store.change(claimed, {**claimed['value'], 'progress': progress, 'updated_at': now()})
            if refreshed:
                claimed = refreshed
        store.change(claimed, {**claimed['value'], **outcome, 'updated_at': now()})
        with core.jobs_lock:
            core.jobs.pop(job['id'], None)
        # Remove only this validated job's temporary files after durable success.
        if outcome.get('status') == 'complete' and ID.fullmatch(job['id']):
            job_dir = (core.MEDIA_DIR / job['id']).resolve()
            if job_dir.parent == core.MEDIA_DIR.resolve() and job_dir.exists():
                shutil.rmtree(job_dir, ignore_errors=True)

    def worker():
        try:
            from .video_runtime import prepare_runtime
            prepare_runtime()
        except Exception:
            app.logger.exception('Video runtime initialization failed')
        while True:
            try:
                for status in ['drafting', 'processing']:
                    for row in store.list(status=status):
                        age = time.time() - datetime.fromisoformat(row['value']['updated_at']).timestamp()
                        if age > 180:
                            store.change(row, {**row['value'], 'status': 'error', 'updated_at': now(),
                                'note': 'Máy chủ đã ngắt tác vụ. Bạn có thể dựng lại từ kịch bản đã lưu.'})
                rows = store.list(status='queued_draft') + store.list(status='queued')
                for row in sorted(rows, key=lambda r: r['value']['created_at']):
                    run_one(row)
            except Exception:
                app.logger.exception('Video queue check failed')
            wake.wait(20)
            wake.clear()

    app.register_blueprint(bp)
    app.extensions['teacher_videos'] = {'run_one': run_one, 'store': store}

    @app.get('/health/video-studio')
    def video_tools_health():
        tools_ready = bool(store.ready and shutil.which('ffmpeg') and shutil.which('ffprobe'))
        return jsonify(feature='teacher-video-studio', tools_ready=tools_ready), 200 if tools_ready else 503

    if start_worker and store.ready and os.getenv('VIDEO_WORKER_ENABLED', '1') != '0':
        os.environ['ALLOW_DEMO_FALLBACK'] = '0'
        os.environ.setdefault('GEMINI_MODEL', 'gemini-2.5-flash')
        os.environ.setdefault('TTS_PROVIDER', 'gtts')
        os.environ.setdefault('RENDER_WORKERS', '1')
        threading.Thread(target=worker, daemon=True, name='teacher-video-queue').start()
    return bp
