"""One catalog for the library and documents: curated assets plus published jobs."""
import json
import re
from pathlib import Path
from .video_store import VideoStore

CATALOG = Path(__file__).resolve().parents[1] / 'data/video_lessons.json'
PUBLISHED_ID = re.compile(r'^teacher-([0-9a-f]{10})$')


def curated_lessons(path=CATALOG):
    path = Path(path)
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else []


def published_lesson(job):
    publication = job.get('publication') or {}
    if (job.get('status') != 'complete' or not job.get('object_key')
            or publication.get('published') is not True):
        return None
    return {
        'id': 'teacher-' + job['id'], 'title': publication['title'],
        'grade': publication['grade'], 'group': publication['group'],
        'description': publication.get('description', ''),
        'teacher_id': job.get('owner_id'), 'object_key': job['object_key'],
        'duration': job.get('duration_seconds') or 0, 'size_bytes': None,
        'poster': 'icons/logo-phyedu.png', 'source': None,
    }


def all_lessons(store=None, path=CATALOG):
    store = store or VideoStore()
    lessons = curated_lessons(path)
    for job in store.list_published():
        lesson = published_lesson(job)
        if lesson:
            lessons.append(lesson)
    return lessons


def find_lesson(lesson_id, store, path=CATALOG):
    match = PUBLISHED_ID.fullmatch(lesson_id)
    if match:
        row = store.get(match.group(1))
        return published_lesson(row['value']) if row else None
    return next((item for item in curated_lessons(path) if item['id'] == lesson_id), None)
