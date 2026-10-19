"""Published lessons for signed-in students and teachers; MP4s remain private."""
from pathlib import Path
from flask import Blueprint, abort, redirect, render_template, session, url_for, request
from .video_store import VideoStore

from .video_catalog import CATALOG, all_lessons, find_lesson

def published_video_documents(store=None):
    rows = all_lessons(store)
    return [dict(item, doc_type='lecture', link_type='video_lesson',
                 description=item.get('description') or item['group']) for item in rows]

def register_video_library(app, get_user, store=None, catalog_path=None):
    store = store or VideoStore()
    path = Path(catalog_path or CATALOG)
    bp = Blueprint('video_library', __name__, url_prefix='/video-lessons')

    def lessons():
        return all_lessons(store, path)

    @bp.errorhandler(RuntimeError)
    def unavailable(error):
        return 'Kho video đang bận. Bạn vui lòng thử lại sau.', 503

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
        lesson = find_lesson(lesson_id, store, path)
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
        lesson = find_lesson(lesson_id, store, path)
        if not lesson:
            abort(404)
        try:
            return redirect(store.signed_url(lesson['object_key']), code=302)
        except RuntimeError:
            return 'Kho video đang bận. Bạn vui lòng thử lại sau.', 503

    app.register_blueprint(bp)
    @app.get('/health/video-library')
    def library_health():
        # Check the actual published object, rather than only checking env vars.
        try:
            items = lessons()
            if not items:
                return {'ready': False, 'reason': 'empty_catalog'}, 503
            store.signed_url(items[0]['object_key'])
            return {'ready': True, 'lessons': len(items)}, 200
        except RuntimeError as error:
            return {'ready': False, 'reason': 'storage_unavailable'}, 503
    return bp
