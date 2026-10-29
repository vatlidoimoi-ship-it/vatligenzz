"""Practice activities backed by the reviewed, Word-derived grade-11 bank."""
import json
from functools import lru_cache
from pathlib import Path

from flask import Blueprint, abort, render_template


@lru_cache(maxsize=1)
def activity_catalog():
    path = Path(__file__).resolve().parents[1] / 'data/docx_exams_grade11.json'
    bank = json.loads(path.read_text(encoding='utf-8'))
    chapters = {}
    for exam in bank['exams']:
        if exam.get('review_status') != 'passed' or exam.get('grade') != '11':
            continue
        source = exam['source_file']
        chapter = chapters.setdefault(source, {'source': source, 'questions': []})
        for question in exam['questions']:
            options = question.get('options', {})
            answer = question.get('correct_answer')
            if set(options) != set('ABCD') or answer not in options:
                continue
            if not question.get('explanation') or not question.get('source_paragraph'):
                continue
            chapter['questions'].append({
                'question': question['question'], 'options': options,
                'answer': answer, 'explanation': question['explanation'],
                'paragraph': question['source_paragraph'],
                'source': source, 'difficulty': question.get('difficulty', ''),
            })
    return [chapter for chapter in chapters.values() if chapter['questions']]


def register_game_activities(app, login_required):
    activities = Blueprint('game_activities', __name__)

    @activities.get('/game/activities/<mode>')
    @login_required
    def play(mode):
        if mode not in ('challenge', 'flashcards'):
            abort(404)
        return render_template('game_activities.html', mode=mode,
                               chapters=activity_catalog())

    app.register_blueprint(activities)
