"""Integration tests use fake persistence and stub the encoder: zero video renders."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from utils.teacher_videos import register_teacher_videos, validated_script


class MemoryStore:
    ready = True
    def __init__(self):
        self.rows = {}
        self.counter = 0
    def create(self, value):
        self.counter += 1
        self.rows[value['id']] = {'value': copy.deepcopy(value), 'updated_at': str(self.counter)}
    def get(self, job_id):
        return copy.deepcopy(self.rows.get(job_id))
    def list(self, owner=None, status=None):
        return [copy.deepcopy(r) for r in self.rows.values()
                if (owner is None or r['value']['owner_id'] == owner)
                and (status is None or r['value']['status'] == status)]
    def change(self, row, value):
        if self.rows[value['id']]['updated_at'] != row['updated_at']:
            return None
        self.create(value)
        return self.get(value['id'])
    def signed_url(self, key):
        return 'https://storage.example/signed/' + key
    def upload(self, job_id, path):
        raise AssertionError('No real upload allowed in tests')


class TeacherVideoTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder=str(ROOT / 'templates'), static_folder=str(ROOT / 'static'))
        self.app.secret_key = 'test-only'
        self.app.add_url_rule('/login', 'login', lambda: 'login')
        self.app.add_url_rule('/teacher/dashboard', 'teacher_dashboard', lambda: 'dashboard')
        self.store = MemoryStore()
        users = {'t1': {'role':'teacher'}, 't2': {'role':'teacher'}, 's1': {'role':'student'}}
        register_teacher_videos(self.app, users.get, self.store, start_worker=False)
        self.client = self.app.test_client()
        self.login()
        self.script = {'problem':'Một câu hỏi vật lí đủ nội dung.', 'design_template':'studio',
                       'steps':[{'title':'Giải thích','slide_text':'Đáp án C',
                                 'narration':'Đây là lời giải thích chi tiết cho đáp án C.', 'latex':''}]}
        self.store.create({'id':'1234567890','owner_id':'t1','status':'script_ready',
                           'script':self.script,'problem':self.script['problem'], 'created_at':'2026-10-13T00:00:00+00:00'})

    def login(self, user='t1'):
        with self.client.session_transaction() as state:
            state.clear()
            if user:
                state['user_id'] = user
                state['video_csrf'] = 'test-csrf'

    def post(self, path, value):
        return self.client.post('/teacher/videos' + path, json=value, headers={'X-CSRF-Token':'test-csrf'})

    def test_login_and_teacher_role_required(self):
        self.login(None)
        self.assertEqual(self.client.get('/teacher/videos/jobs').status_code, 401)
        self.login('s1')
        self.assertEqual(self.client.get('/teacher/videos/jobs').status_code, 403)

    def test_teacher_cannot_read_render_or_play_another_job(self):
        self.login('t2')
        self.assertEqual(self.client.get('/teacher/videos/jobs').json['items'], [])
        for suffix in ['', '/play']:
            self.assertEqual(self.client.get('/teacher/videos/jobs/1234567890' + suffix).status_code, 404)
        self.assertEqual(self.post('/jobs/1234567890/render', self.script).status_code, 404)

    def test_csrf_required(self):
        self.assertEqual(self.client.post('/teacher/videos/jobs', json={'problem':'Một đề đủ dài để tạo.'}).status_code, 403)

    def test_create_persists_draft_queue(self):
        response = self.post('/jobs', {'problem':'Một đề bài mới có đầy đủ dữ kiện.'})
        self.assertEqual(response.status_code, 202)
        job = response.json['job']
        self.assertEqual(self.store.get(job['id'])['value']['status'], 'queued_draft')
        self.assertEqual(self.post('/jobs', {'problem':'Một đề bài khác đủ dài.'}).status_code, 409)

    def test_render_queue_and_double_click_guard(self):
        with patch('utils.teacher_videos.shutil.which', return_value='fake-tool'):
            self.assertEqual(self.post('/jobs/1234567890/render', self.script).status_code, 202)
            self.assertEqual(self.post('/jobs/1234567890/render', self.script).status_code, 409)
        self.assertEqual(self.store.get('1234567890')['value']['script']['steps'][0]['slide_text'], 'Đáp án C')

    def test_bad_scripts_and_local_paths(self):
        for payload in [None, [], {}, {'steps':[]}, {'steps':[{'narration':7}]}]:
            with self.assertRaises(ValueError):
                validated_script(payload, self.script)
        payload = copy.deepcopy(self.script)
        payload['steps'][0]['image_ref'] = 'file:///etc/passwd'
        payload['history_assets'] = [{'path':'../../secret'}]
        clean = validated_script(payload, self.script)
        self.assertNotIn('history_assets', clean)
        self.assertNotIn('image_ref', clean['steps'][0])

    def test_missing_tools_does_not_enqueue_render(self):
        with patch('utils.teacher_videos.shutil.which', return_value=None):
            self.assertEqual(self.post('/jobs/1234567890/render', self.script).status_code, 503)
        self.assertEqual(self.store.get('1234567890')['value']['status'], 'script_ready')

    def test_preview_uses_edited_script_without_encoder(self):
        from botvideo import core
        payload = copy.deepcopy(self.script)
        payload['steps'][0]['title'] = 'Tiêu đề đã chỉnh'
        payload['preview_index'] = 0
        def fake_image(html, png):
            self.assertIn('Tiêu đề đã chỉnh', html.read_text(encoding='utf-8'))
            png.write_bytes(b'\x89PNG\r\n\x1a\n')
            return True
        with patch.object(core, 'render_scene_png_with_playwright', side_effect=fake_image), \
             patch.object(core, 'safe_render_job') as encoder:
            response = self.post('/jobs/1234567890/preview', payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'image/png')
            encoder.assert_not_called()
        self.assertEqual(self.store.get('1234567890')['value']['status'], 'script_ready')
        self.login('t2')
        self.assertEqual(self.post('/jobs/1234567890/preview',payload).status_code,404)

    def test_private_play_requires_complete(self):
        self.assertEqual(self.client.get('/teacher/videos/jobs/1234567890/play').status_code, 404)
        row = self.store.get('1234567890')
        self.store.change(row, {**row['value'], 'status':'complete','object_key':'1234567890/result.mp4'})
        response = self.client.get('/teacher/videos/jobs/1234567890/play')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.startswith('https://storage.example/signed/'))
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_draft_worker_and_claim_are_durable(self):
        from botvideo import core
        row = self.store.get('1234567890')
        row = self.store.change(row, {**row['value'], 'status':'queued_draft'})
        run_one = self.app.extensions['teacher_videos']['run_one']
        with patch.object(core, 'ask_gemini', return_value=self.script) as ai:
            run_one(row)
            run_one(row)  # stale claim cannot execute twice
            self.assertEqual(ai.call_count, 1)
        self.assertEqual(self.store.get('1234567890')['value']['status'], 'script_ready')

    def test_upload_failure_is_not_complete(self):
        from botvideo import core
        row = self.store.get('1234567890')
        row = self.store.change(row, {**row['value'], 'status':'queued'})
        def fake_encoder(job_id, script):
            core.jobs[job_id] = {'status':'complete', 'progress':100, 'duration_seconds':30}
        with patch.object(core, 'safe_render_job', side_effect=fake_encoder), \
             patch.object(self.store, 'upload', side_effect=RuntimeError('storage offline')):
            self.app.extensions['teacher_videos']['run_one'](row)
        self.assertEqual(self.store.get('1234567890')['value']['status'], 'error')


if __name__ == '__main__':
    unittest.main()
