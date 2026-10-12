"""Check generated Word-based exams and the real existing submission handler.

No production app import, database access or external AI calls.
"""
import ast
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import types
import unittest
from unittest.mock import patch
from flask import Flask, jsonify, request, session, render_template

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / 'data/docx_exams_grade11.json'


class WordExamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exams = json.loads(BANK.read_text(encoding='utf-8'))['exams']

    def test_matrix_and_unique_content(self):
        self.assertEqual(len(self.exams), 20)
        self.assertEqual(len({e['id'] for e in self.exams}), 20)
        self.assertEqual(sorted(Counter(e['source_file'] for e in self.exams).values()), [5]*4)
        stems = []
        for exam in self.exams:
            self.assertEqual(exam['grade'], '11')
            self.assertEqual(exam['time_limit'], 30)
            self.assertEqual(len(exam['questions']), 20)
            self.assertEqual([q['id'] for q in exam['questions']], list(range(1, 21)))
            self.assertEqual(Counter(q['difficulty'] for q in exam['questions']), {'NB': 6, 'TH': 8, 'VD': 6})
            self.assertEqual(Counter(q['correct_answer'] for q in exam['questions']), dict.fromkeys('ABCD', 5))
            for question in exam['questions']:
                self.assertEqual(set(question['options']), set('ABCD'))
                self.assertEqual(len(set(question['options'].values())), 4)
                self.assertGreater(len(question['explanation']), 30)
                self.assertGreater(len(question['source_quote']), 12)
                self.assertEqual(question['source_file'], exam['source_file'])
                self.assertNotRegex(question['question'], r'<[^>]+>')
                stems.append(re.sub(r'\s+', ' ', question['question'].strip().lower()))
        self.assertEqual(len(stems), len(set(stems)), 'Duplicate questions across exams')

    def test_original_sources_when_available(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from build_docx_exams import source_paragraphs
        if not (ROOT / 'datatm').exists():
            self.skipTest('Original user files are local only')
        for chapter in range(1, 5):
            source, lines = source_paragraphs(chapter)
            paragraphs = dict(lines)
            checksum = hashlib.sha256(source.read_bytes()).hexdigest()
            for exam in self.exams:
                if exam['source_file'] != source.name:
                    continue
                self.assertEqual(exam['source_sha256'], checksum)
                for question in exam['questions']:
                    self.assertEqual(question['source_quote'], paragraphs[int(question['source_paragraph'])])

    def test_actual_submission_route_grades_20_question_exams(self):
        app = Flask(__name__)
        app.secret_key = 'offline-test-only'
        stored = []
        scope = {'app': app, 'request': request, 'session': session, 'jsonify': jsonify,
                 'login_required': lambda f: f, 'validate_subject': lambda s: s == 'li',
                 'is_supported_exam': lambda e: e.get('grade') == '11',
                 'readable_data_file': lambda _: str(BANK), 'writable_data_file': lambda _: 'test-only',
                 'read_json': lambda *_: [], 'write_json': lambda _, rows: stored.extend(rows),
                 'SUBJECTS': {'li': {'name': 'Vật Lý'}}, 'datetime': datetime, 'json': json}
        tree = ast.parse((ROOT / 'app.py').read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'nop_bai_tracnghiem')
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'actual_submission_handler', 'exec'), scope)
        fake_ai = types.ModuleType('utils.gemini_api')
        fake_ai.analyze_exam_results = lambda _: None
        with patch.dict(sys.modules, {'utils.gemini_api': fake_ai}), app.test_client() as client:
            for exam in self.exams:
                for count in [20, 10, 0]:
                    with client.session_transaction() as state:
                        state['user_id'] = 'offline-test'
                        state[f'exam_start_li_{exam["id"]}'] = datetime.now().isoformat()
                    answers = {str(q['id']): q['correct_answer'] for q in exam['questions'][:count]}
                    response = client.post('/tracnghiem/nop-bai', json={'subject': 'li', 'exam_id': exam['id'], 'answers': answers})
                    self.assertEqual(response.status_code, 200)
                    result = response.json['result']
                    self.assertEqual(result['total_score'], count / 2)
                    self.assertEqual(result['multiple_choice']['correct_count'], count)
            self.assertEqual(len(stored), 60)

    def test_all_exams_render_without_exposing_solutions(self):
        app = Flask(__name__, template_folder=str(ROOT / 'templates'))
        app.secret_key = 'offline-render'
        with app.test_request_context('/'):
            app.jinja_env.globals['url_for'] = lambda endpoint, **kwargs: '/test/' + endpoint
            for exam in self.exams:
                html = render_template('baitap.html', exam=exam, subject='li',
                                       subject_name='Vật Lý', subject_icon='⚡', subject_color='#0064B7',
                                       time_limit=30, remaining_time=1800)
                # The base template also has appearance-setting radio buttons.
                self.assertEqual(html.count('name="question_'), 80)
                for question in exam['questions']:
                    self.assertEqual(html.count(f'name="question_{question["id"]}"'), 4)
                self.assertNotIn('correct_answer', html)
                self.assertIn(exam['id'], html)


if __name__ == '__main__':
    unittest.main()
