"""Published lessons for signed-in students and teachers; MP4s remain private."""
import json
from pathlib import Path
from flask import Blueprint, abort, redirect, render_template, session, url_for
from .video_store import VideoStore

CATALOG = Path(__file__).resolve().parents[1] / 'data/video_lessons.json'

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
        return render_template('video_lesson.html', lesson=lesson)

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
