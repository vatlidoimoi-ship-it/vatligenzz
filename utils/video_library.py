"""Published lessons for signed-in students and teachers; MP4s remain private."""
import json
from pathlib import Path
from flask import Blueprint, abort, redirect, render_template, session, url_for, request
from .video_store import VideoStore

CATALOG = Path(__file__).resolve().parents[1] / 'data/video_lessons.json'

def published_video_documents():
    rows = json.loads(CATALOG.read_text(encoding='utf-8')) if CATALOG.exists() else []
    return [dict(item, doc_type='lecture', link_type='video_lesson',
                 description=item['group']) for item in rows]

def register_video_library(app, get_user, store=None, catalog_path=None):
    store = store or VideoStore()
    path = Path(catalog_path or CATALOG)
    bp = Blueprint('video_library', __name__, url_prefix='/video-lessons')

    def lessons():
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else []

    @bp.before_request
    def require_login():
        if not session.get('user_id') or not get_user(session['user_id']):
            return redirect(url_for('login'))

    @bp.after_request
    def no_cache(response):
        response.headers['Cache-Control'] = 'private, no-store'
        return response

    @bp.get('')
    def index():
        return render_template('video_library.html', lessons=lessons())

    @bp.get('/<lesson_id>')
    def watch(lesson_id):
        lesson = next((item for item in lessons() if item['id'] == lesson_id), None)
        if not lesson:
            abort(404)
        back_url = url_for('video_library.index')
        back_label = 'Kho video bài giảng'
        if request.args.get('origin') == 'documents':
            grade = request.args.get('grade', 'all')
            kind = request.args.get('kind', 'lecture')
            back_url = url_for('documents', grade=grade if grade in {'all','10','11','12','hsg'} else 'all',
                               type=kind if kind in {'all','lecture'} else 'lecture')
            back_label = 'Bài giảng trong kho tài liệu'
        return render_template('video_lesson.html', lesson=lesson, back_url=back_url, back_label=back_label)

    @bp.get('/<lesson_id>/play')
    def play(lesson_id):
        lesson = next((item for item in lessons() if item['id'] == lesson_id), None)
        if not lesson:
            abort(404)
        try:
            return redirect(store.signed_url(lesson['object_key']), code=302)
        except RuntimeError:
            return 'Kho video đang bận. Bạn vui lòng thử lại sau.', 503

    app.register_blueprint(bp)
    return bp
