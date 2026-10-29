"""Exercise routes and verify the practice bank still matches supplied Word files."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

from flask import Flask, session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from utils.game_activities import activity_catalog, register_game_activities


class GameActivityTests(unittest.TestCase):
    def test_sources_and_answers(self):
        bank = json.loads((ROOT / 'data/docx_exams_grade11.json').read_text(encoding='utf-8'))
        for exam in bank['exams']:
            source = ROOT / 'datatm' / exam['source_file']
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), exam['source_sha256'])
        catalog = activity_catalog()
        self.assertEqual(len(catalog), 4)
        self.assertEqual(sum(len(c['questions']) for c in catalog), 400)
        for chapter in catalog:
            for question in chapter['questions']:
                self.assertIn(question['answer'], question['options'])
                self.assertTrue(question['explanation'])
                self.assertGreater(question['paragraph'], 0)

    def test_routes_require_login_and_render_both_modes(self):
        app = Flask(__name__, template_folder=str(ROOT / 'templates'))
        app.secret_key = 'test-only'
        # Render the real activity template with a minimal shared layout.
        from jinja2 import ChoiceLoader, DictLoader
        app.jinja_loader = ChoiceLoader([DictLoader({'base.html': '{% block content %}{% endblock %}'}), app.jinja_loader])
        app.add_url_rule('/enter_nickname', 'enter_nickname', lambda: 'lobby')
        def login_required(view):
            from functools import wraps
            @wraps(view)
            def wrapped(*args, **kwargs):
                if not session.get('user_id'):
                    return 'login required', 401
                return view(*args, **kwargs)
            return wrapped
        register_game_activities(app, login_required)
        client = app.test_client()
        self.assertEqual(client.get('/game/activities/challenge').status_code, 401)
        with client.session_transaction() as state:
            state['user_id'] = 'student'
        for mode in ('challenge', 'flashcards'):
            response = client.get('/game/activities/' + mode)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'activity-data', response.data)
        self.assertEqual(client.get('/game/activities/unknown').status_code, 404)


if __name__ == '__main__':
    unittest.main()
