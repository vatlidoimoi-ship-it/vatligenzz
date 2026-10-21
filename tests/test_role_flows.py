"""Role/learning-flow regressions with temporary storage and no external services.

Run directly in a separate process: python -B tests/test_role_flows.py
"""
import ast
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
TEMP = tempfile.TemporaryDirectory(prefix='phyedu-flow-tests-')
ENV = patch.dict(os.environ, {
    'DATA_BACKEND': 'file', 'PERSISTENT_DIR': TEMP.name,
    'DATA_DIR': TEMP.name + '/data', 'STATE_DIR': TEMP.name,
    'FORUM_UPLOAD_DIR': TEMP.name + '/uploads', 'VIDEO_WORKER_ENABLED': '0',
    'SUPABASE_URL': '', 'SUPABASE_SERVICE_ROLE_KEY': '', 'SECRET_KEY': 'test-only',
})
ENV.start()
DATA = Path(TEMP.name) / 'data'
DATA.mkdir()
for path in (ROOT / 'data').glob('*.json'):
    (DATA / path.name).write_text('[]', encoding='utf-8')
(DATA / 'li.json').write_text('{"exams":[]}', encoding='utf-8')
fake_ai = types.ModuleType('utils.gemini_api')
for node in ast.parse((ROOT / 'utils/gemini_api.py').read_text(encoding='utf-8-sig')).body:
    if isinstance(node, ast.FunctionDef):
        setattr(fake_ai, node.name, lambda *a, **kw: 'AI stub')
sys.modules['utils.gemini_api'] = fake_ai
NETWORK = patch('requests.sessions.Session.request', side_effect=AssertionError('No network in tests'))
NETWORK.start()
with patch('dotenv.load_dotenv', return_value=False):
    import app as web


class RoleFlowTests(unittest.TestCase):
    def setUp(self):
        web.app.config.update(TESTING=True)
        self.client = web.app.test_client()
        users = [{'id': role, 'role': 'teacher' if role == 'teacher2' else role,
                  'username': role, 'email': role + '@example.test', 'password': 'unused'}
                 for role in ['student', 'teacher', 'teacher2', 'admin']]
        web.save_users(users)
        self.course = {'id': 'course_a', 'teacher_id': 'teacher', 'title': 'Test course',
                       'description': '', 'grade': '10', 'created_at': '2026-10-20',
                       'lessons': [{'id': 'lesson_a', 'title': 'Lesson', 'video_url': '',
                                    'document_url': '', 'questions': [
                                        {'question': 'Choose', 'options': ['A', 'B'],
                                         'correct_answer': 'A', 'explanation': 'ANSWER_SECRET'}]}]}
        for file in [web.db.submissions_file, web.db.progress_file, web.db.chat_messages_file,
                     web.db.documents_file, web.SCORES_FILE]:
            web.write_json(file, [])
        web.write_json(web.GAME_ATTEMPTS_FILE, {})
        web.db._save_json(web.db.courses_file, [self.course])
        web._save_subject_exam_data('li', {'exams': []})
        self.login('student')

    def login(self, role):
        with self.client.session_transaction() as state:
            state.clear()
            if role:
                state.update(user_id=role, username=role,
                             role='teacher' if role == 'teacher2' else role)

    def test_stale_login_cookie_does_not_redirect_forever(self):
        with self.client.session_transaction() as state:
            state.update(user_id='removed-account', username='Old name', role='admin')
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as state:
            self.assertNotIn('user_id', state)

        with self.client.session_transaction() as state:
            state.update(user_id='student', username='Old name', role='admin')
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request.path, '/student/dashboard')
        with self.client.session_transaction() as state:
            self.assertEqual(state['role'], 'student')
            self.assertEqual(state['username'], 'student')

    def post(self, path, **data):
        return self.client.post(path, json=data)

    def test_private_ai_never_in_room_or_polling(self):
        mid = web.db.add_chat_message({'author_id': 'teacher', 'author_name': 'teacher',
                                      'content': 'PRIVATE_PROMPT', 'response': 'PRIVATE_REPLY'})
        web.db.add_chat_message({'author_id': 'teacher', 'author_name': 'teacher', 'content': 'PUBLIC'})
        for path in ['/chat', '/api/chat/messages']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'PRIVATE', response.data)
            self.assertIn(b'PUBLIC', response.data)
        self.assertEqual(self.post('/api/chat/send', content='reply', reply_to=mid).status_code, 404)
        self.assertEqual(self.client.get('/api/chat/history').json['messages'], [])
        self.login('teacher')
        self.assertEqual(len(self.client.get('/api/chat/history').json['messages']), 1)

    def test_legacy_ai_records_are_private(self):
        web.write_json(web.db.chat_messages_file, [
            {'id': 'legacy', 'author_id': 'student', 'response': '', 'content': 'PRIVATE'}])
        self.assertEqual(web.db.get_all_chat_messages(), [])

    def test_only_exam_owner_can_delete(self):
        web._save_subject_exam_data('li', {'exams': [
            {'id': 'owned', 'grade': '10', 'created_by': 'teacher'},
            {'id': 'catalog', 'grade': '10', 'created_by': None}]})
        self.login('teacher2')
        self.assertEqual(self.post('/teacher/exams/delete', subject='li', exam_id='owned').status_code, 403)
        self.login('teacher')
        self.assertEqual(self.post('/teacher/exams/delete', subject='li', exam_id='catalog').status_code, 403)
        self.assertTrue(self.post('/teacher/exams/delete', subject='li', exam_id='owned').json['success'])
        self.assertEqual(len(web._load_subject_exam_data('li')['exams']), 1)

    def test_answers_hidden_from_course_and_exercises(self):
        for role in ['student', 'teacher2']:
            self.login(role)
            for path in ['/api/course/course_a', '/exercises', '/course/course_a']:
                response = self.client.get(path)
                self.assertNotIn(b'correct_answer', response.data)
                self.assertNotIn(b'ANSWER_SECRET', response.data)
        for role in ['teacher', 'admin']:
            self.login(role)
            self.assertIn(b'correct_answer', self.client.get('/api/course/course_a').data)

    def test_invalid_lesson_does_not_write(self):
        for endpoint in ['/submit_exercise', '/update_progress']:
            response = self.post(endpoint, course_id='course_a', lesson_id='missing', answers={'0': 'A'})
            self.assertEqual(response.status_code, 404)
        self.assertEqual(web.read_json(web.db.submissions_file, []), [])
        self.assertEqual(web.read_json(web.db.progress_file, []), [])

    def test_bad_answers_rejected(self):
        for answers in [[], {'0': 123}]:
            self.assertEqual(self.post('/submit_exercise', course_id='course_a',
                                      lesson_id='lesson_a', answers=answers).status_code, 400)

    def start_game(self):
        web.save_game_bank({'topics': [{'id': 'topic', 'title': 'Topic', 'grade': 'Lớp 10',
                                       'questions': [{'question': 'Q', 'options': ['A', 'B'], 'answer': 'A'}]}]})
        with self.client.session_transaction() as state:
            state['game_topic_id'] = 'topic'
        return self.client.get('/get_questions')

    def test_game_server_scores_and_blocks_replays(self):
        response = self.start_game()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('answer', response.json[0])
        self.assertEqual(self.post('/submit_score', score=999, total=999).status_code, 409)
        result = self.post('/game/answer', index=0, answer='B', score=999)
        self.assertEqual(result.json['score'], 0)
        self.assertEqual(self.post('/game/answer', index=0, answer='A').status_code, 409)
        self.assertEqual(self.post('/submit_score', score=999).json['score'], 0)
        self.post('/submit_score', score=999)
        scores = web.read_json(web.SCORES_FILE, [])
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0]['score'], 0)

    def test_game_timeout_and_cross_user(self):
        self.start_game()
        attempts = web.read_json(web.GAME_ATTEMPTS_FILE, {})
        attempts['student']['opened_at'] = (datetime.now() - timedelta(seconds=30)).isoformat()
        web.write_json(web.GAME_ATTEMPTS_FILE, attempts)
        self.assertEqual(self.post('/game/answer', index=0, answer='A').json['score'], 0)
        self.login('teacher')
        self.assertEqual(self.post('/submit_score').status_code, 409)

    def test_role_dashboard_access(self):
        for role in ['student', 'teacher', 'admin']:
            self.login(role)
            self.assertEqual(self.client.get('/').location,
                             '/admin' if role == 'admin' else '/' + role + '/dashboard')
            if role not in {'teacher', 'admin'}:
                self.assertEqual(self.client.get('/teacher/exams').status_code, 302)
            else:
                self.assertEqual(self.client.get('/teacher/exams').status_code, 200)
            if role != 'admin':
                self.assertEqual(self.client.get('/admin/shop').status_code, 302)

    def test_submission_grade_persisted_and_teacher_feedback_visible(self):
        result = self.post('/submit_exercise', course_id='course_a', lesson_id='lesson_a', answers={'0': 'A'})
        self.assertEqual(result.json['score'], 100)
        submission_id = result.json['submission_id']
        self.assertEqual(web.read_json(web.db.submissions_file, [])[0]['score'], 100)
        self.assertEqual(web.db.get_student_progress('student')[0]['completed_lessons'], ['lesson_a'])
        self.login('teacher2')
        self.assertEqual(self.post(f'/teacher/submissions/{submission_id}/grade', score=40).status_code, 404)
        self.login('teacher')
        result = self.post(f'/teacher/submissions/{submission_id}/grade', score=85.5, feedback='REVIEWED_FEEDBACK')
        self.assertTrue(result.json['success'])
        self.assertIn(b'85.5', self.client.get('/teacher/view_submissions').data)
        self.login('student')
        response = self.client.get('/exercises')
        self.assertIn(b'85.5', response.data)
        self.assertIn(b'REVIEWED_FEEDBACK', response.data)
        self.assertEqual(self.post(f'/teacher/submissions/{submission_id}/grade', score=100).status_code, 302)

    def test_invalid_grade_does_not_change_saved_score(self):
        result = self.post('/submit_exercise', course_id='course_a', lesson_id='lesson_a', answers={'0': 'B'})
        self.login('teacher')
        for score in [-1, 101, True, '100', float('nan'), float('inf')]:
            response = self.post(f"/teacher/submissions/{result.json['submission_id']}/grade", score=score)
            self.assertEqual(response.status_code, 400)
        self.assertEqual(web.read_json(web.db.submissions_file, [])[0]['score'], 0)

    def test_missing_answer_key_is_pending_not_zero(self):
        del self.course['lessons'][0]['questions'][0]['correct_answer']
        web.db._save_json(web.db.courses_file, [self.course])
        response = self.post('/submit_exercise', course_id='course_a', lesson_id='lesson_a', answers={'0': 'A'})
        self.assertTrue(response.json['success'])
        self.assertNotIn('score', response.json)
        saved = web.read_json(web.db.submissions_file, [])[0]
        self.assertEqual(saved['grading_status'], 'pending')

    def test_progress_can_be_unmarked(self):
        self.post('/update_progress', course_id='course_a', lesson_id='lesson_a', completed=True)
        self.post('/update_progress', course_id='course_a', lesson_id='lesson_a', completed=False)
        self.assertEqual(web.db.get_student_progress('student')[0]['completed_lessons'], [])

    def seed_exam(self):
        exam = {'id': 'exam_test', 'title': 'Test exam', 'grade': '10', 'time_limit': 1,
                'questions': [{'id': 1, 'number': 1, 'question': 'Question',
                               'options': {'A': 'Yes', 'B': 'No'}, 'correct_answer': 'A'}]}
        web._save_subject_exam_data('li', {'exams': [exam]})
        return exam

    def test_exam_submit_deadline_grace_and_expiry(self):
        self.seed_exam()
        for elapsed, expected in [(30, 200), (62, 200), (75, 403)]:
            with self.client.session_transaction() as state:
                state['exam_start_li_exam_test'] = (datetime.now() - timedelta(seconds=elapsed)).isoformat()
            response = self.post('/tracnghiem/nop-bai', subject='li', exam_id='exam_test', answers={'1': 'A'})
            self.assertEqual(response.status_code, expected)
            if expected == 200:
                self.assertEqual(response.json['result']['total_score'], 10)
            self.assertEqual(self.post('/tracnghiem/nop-bai', subject='li', exam_id='exam_test', answers={'1': 'A'}).status_code, 403)

    def test_teacher_sees_result_after_submitting_catalog_exam(self):
        exam = self.seed_exam()
        exam['grade'] = '11'
        web._save_subject_exam_data('li', {'exams': [exam]})
        self.login('teacher')
        page = self.client.get('/tracnghiem/lam-bai/li/exam_test')
        self.assertEqual(page.status_code, 200)
        with patch('utils.gemini_api.analyze_exam_results', side_effect=AssertionError('AI must not block scoring')):
            submitted = self.post('/tracnghiem/nop-bai', subject='li', exam_id='exam_test', answers={'1': 'B'})
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.json['result']['total_score'], 0)
        result = self.client.get('/tracnghiem/ket-qua/li/exam_test')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'request-ai-analysis', result.data)
        history = self.client.get('/tracnghiem/lich-su')
        self.assertEqual(history.status_code, 200)
        with patch('utils.gemini_api.analyze_exam_results', return_value={
            'overall_assessment': 'Review', 'strengths': '', 'weaknesses': '',
            'study_plan': '', 'encouragement': ''}):
            feedback = self.post('/tracnghiem/phan-tich/li/exam_test')
        self.assertEqual(feedback.status_code, 200)
        self.assertEqual(self.client.get('/tracnghiem/ket-qua/li/exam_test').status_code, 200)

    def test_exam_history_sorts_day_month_year_dates_chronologically(self):
        first = self.seed_exam()
        second = {**first, 'id': 'exam_april', 'title': 'April exam'}
        first['title'] = 'March exam'
        web._save_subject_exam_data('li', {'exams': [first, second]})
        web.write_json(web.writable_data_file('exam_results.json'), [
            {'user_id': 'student', 'subject': 'li', 'exam_id': first['id'],
             'exam_title': first['title'], 'submitted_at': '31/03/2026 09:00:00',
             'result': {'total_score': 8}},
            {'user_id': 'student', 'subject': 'li', 'exam_id': second['id'],
             'exam_title': second['title'], 'submitted_at': '01/04/2026 09:00:00',
             'result': {'total_score': 9}},
        ])
        page = self.client.get('/tracnghiem/lich-su')
        self.assertEqual(page.status_code, 200)
        self.assertLess(page.data.index(b'April exam'), page.data.index(b'March exam'))

    def test_admin_overview_counts_learning_activity_by_month_and_grade(self):
        self.seed_exam()
        web.db._save_json(web.db.progress_file, [{
            'user_id': 'student', 'course_id': 'course_a',
            'completed_lessons': ['lesson_a'], 'last_updated': '2026-07-15T10:00:00',
        }])
        web.db._save_json(web.db.submissions_file, [{
            'id': 'sub_a', 'user_id': 'student', 'course_id': 'course_a',
            'exercise_id': 'lesson_a', 'submitted_at': '2026-07-15T10:00:00',
        }])
        web.write_json(web.writable_data_file('exam_results.json'), [
            {'user_id': 'student', 'subject': 'li', 'exam_id': 'exam_test',
             'submitted_at': '15/03/2026 09:00:00'},
            {'user_id': 'teacher', 'subject': 'li', 'exam_id': 'exam_test',
             'submitted_at': '20/10/2026 09:00:00'},
        ])
        stats = web.admin_dashboard_stats()
        self.assertEqual(stats['exam_attempts'], 1)
        self.assertEqual(stats['submissions'], 1)
        self.assertEqual(stats['completed_lessons'], 1)
        self.assertEqual(stats['grade_rows'][0]['attempts'], 1)
        self.assertEqual(stats['reporting_window'], 'T3/2026 – T9/2026')
        self.assertEqual(stats['monthly_rows'][0]['exams'], 1)
        self.assertEqual(stats['monthly_rows'][4]['submissions'], 1)
        self.assertEqual([row['cumulative_exams'] for row in stats['monthly_rows']], [1] * 7)
        self.assertEqual([row['cumulative_submissions'] for row in stats['monthly_rows']], [0, 0, 0, 0, 1, 1, 1])
        self.assertTrue(stats['exam_chart_points'].startswith('0,100 '))
        self.assertTrue(stats['exam_chart_points'].endswith('600.0,0.0'))
        self.login('admin')
        page = self.client.get('/admin/forum-reports')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Lũy kế hoạt động học tập'.encode(), page.data)

    def test_admin_manages_courses_and_documents_without_taking_ownership(self):
        self.login('admin')
        for path in ['/teacher/dashboard', '/teacher/edit_course/course_a', '/teacher/add_document',
                     '/teacher/students_progress', '/teacher/view_submissions', '/teacher/game_questions', '/teacher/videos']:
            self.assertEqual(self.client.get(path).status_code, 200, path)
        response = self.post('/teacher/edit_course/course_a', title='Updated by admin', grade='10',
                             lessons=self.course['lessons'], teacher_id='admin', id='hijacked')
        self.assertTrue(response.json['success'])
        course = web.db.get_course_by_id('course_a')
        self.assertEqual(course['teacher_id'], 'teacher')
        self.assertEqual(course['title'], 'Updated by admin')
        document_id = web.db.add_document({'title': 'Teacher document', 'grade': '10',
                                          'url': 'https://example.test/doc', 'teacher_id': 'teacher'})
        self.assertTrue(self.post('/teacher/edit_document/' + document_id, title='Admin revision').json['success'])
        self.assertEqual(web.db.get_document_by_id(document_id)['teacher_id'], 'teacher')
        self.assertTrue(self.post('/teacher/delete_document/' + document_id).json['success'])
        self.assertTrue(self.post('/teacher/delete_course/course_a').json['success'])

    def test_admin_can_grade_and_delete_seed_exam(self):
        response = self.post('/submit_exercise', course_id='course_a', lesson_id='lesson_a', answers={'0': 'B'})
        self.seed_exam()
        self.login('admin')
        self.assertTrue(self.post('/teacher/submissions/' + response.json['submission_id'] + '/grade', score=75).json['success'])
        self.assertEqual(web.read_json(web.db.submissions_file, [])[0]['graded_by'], 'admin')
        self.assertTrue(self.post('/teacher/exams/delete', subject='li', exam_id='exam_test').json['success'])

    def test_teacher_remains_scoped_to_own_courses(self):
        self.login('teacher2')
        self.assertEqual(self.client.get('/teacher/edit_course/course_a').status_code, 302)
        self.assertFalse(self.post('/teacher/delete_course/course_a').json['success'])
        self.assertNotIn(b'Test course', self.client.get('/teacher/dashboard').data)
        self.login('admin')
        self.assertIn(b'Test course', self.client.get('/teacher/dashboard').data)


if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        NETWORK.stop()
        ENV.stop()
        TEMP.cleanup()
