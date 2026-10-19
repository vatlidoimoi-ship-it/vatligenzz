"""Run separately: python -B tests/test_video_publication.py"""
import unittest
from unittest.mock import Mock, patch
import test_role_flows as fixtures
from video_publication_support import attach_store
from utils.video_store import VideoStore

web = fixtures.web


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.RoleFlowTests()
        self.fixture.setUp()
        self.client = self.fixture.client
        self.memory, self.stack = attach_store(web)
        self.addCleanup(self.stack.close)
        self.login('teacher')

    def login(self, role):
        self.fixture.login(role)
        with self.client.session_transaction() as state:
            state['video_csrf'] = 'csrf'

    def publish(self, **overrides):
        payload = {'published': True, 'title': 'Published lesson', 'grade': '10',
                   'group': 'Mechanics', 'description': 'Student description'}
        payload.update(overrides)
        return self.client.post('/teacher/videos/jobs/1234567890/publication', json=payload,
                                headers={'X-CSRF-Token': 'csrf'})

    def test_publish_student_discovery_revoke_and_republish(self):
        self.login('student')
        self.assertEqual(self.client.get('/video-lessons/teacher-1234567890/play').status_code, 404)
        self.login('teacher')
        result = self.publish(object_key='attacker/file.mp4')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['job']['lesson_url'], '/video-lessons/teacher-1234567890')
        self.login('student')
        for path in ['/video-lessons', '/documents?grade=10&type=lecture', '/video-lessons/teacher-1234567890']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(b'Published lesson', response.data)
            self.assertNotIn(b'PRIVATE_SCRIPT_NOT_FOR_CATALOG', response.data)
        response = self.client.get('/video-lessons/teacher-1234567890/play')
        self.assertTrue(response.location.endswith('1234567890/result.mp4'))
        self.assertIn('no-store', response.headers['Cache-Control'])
        self.login('teacher')
        self.assertEqual(self.publish(published=False).status_code, 200)
        self.login('student')
        self.assertNotIn(b'Published lesson', self.client.get('/video-lessons').data)
        for path in ['/video-lessons/teacher-1234567890', '/video-lessons/teacher-1234567890/play']:
            self.assertEqual(self.client.get(path).status_code, 404)
        self.login('teacher')
        self.assertEqual(self.client.get('/teacher/videos/jobs/1234567890/play').status_code, 302)
        self.assertEqual(self.publish(title='Revised title').status_code, 200)
        self.assertEqual(len(self.memory.list_published()), 1)

    def test_publication_requires_staff_owner_or_admin_and_csrf(self):
        self.assertEqual(self.client.post('/teacher/videos/jobs/1234567890/publication', json={}).status_code, 403)
        for role, status in [('student', 403), ('teacher2', 404), ('admin', 200)]:
            self.login(role)
            self.assertEqual(self.publish().status_code, status)
        self.assertEqual(self.memory.get('1234567890')['value']['owner_id'], 'teacher')
        self.assertEqual(len(self.client.get('/teacher/videos/jobs').json['items']), 1)
        self.assertEqual(self.publish(published=False).status_code, 200)
        self.login(None)
        self.assertEqual(self.publish().status_code, 401)

    def test_unfinished_video_cannot_be_published(self):
        row = self.memory.get('1234567890')
        self.memory.change(row, {**row['value'], 'status': 'script_ready'})
        self.assertEqual(self.publish().status_code, 409)
        self.assertEqual(self.memory.list_published(), [])

    def test_invalid_metadata_rejected(self):
        for values in [{'title': ''}, {'title': 'x' * 181}, {'group': []}, {'grade': '9'},
                       {'grade': []}, {'description': 42}, {'published': 'true'}]:
            self.assertEqual(self.publish(**values).status_code, 400, values)
        self.assertNotIn('publication', self.memory.get('1234567890')['value'])

    def test_concurrent_update_does_not_report_success(self):
        store = web.app.extensions['teacher_videos']['store']
        with patch.object(store, 'change', return_value=None):
            self.assertEqual(self.publish().status_code, 409)
        self.assertNotIn('publication', self.memory.get('1234567890')['value'])

    def test_storage_failure_is_visible_without_private_details(self):
        store = web.app.extensions['teacher_videos']['store']
        with patch.object(store, 'change', side_effect=RuntimeError('SECRET_INTERNAL')):
            response = self.publish()
            self.assertEqual(response.status_code, 503)
            self.assertNotIn(b'SECRET_INTERNAL', response.data)
        self.login('student')
        with patch.object(store, 'list_published', side_effect=RuntimeError('SECRET_INTERNAL')):
            self.assertEqual(self.client.get('/video-lessons').status_code, 503)
            response = self.client.get('/documents')
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'SECRET_INTERNAL', response.data)

    def test_catalog_pagination_uses_public_projection(self):
        store = VideoStore()
        store.ready = True
        first = Mock(); first.json.return_value = [{'id': str(i)} for i in range(100)]
        second = Mock(); second.json.return_value = [{'id': 'last'}]
        with patch.object(store, 'call', side_effect=[first, second]) as call:
            self.assertEqual(len(store.list_published()), 101)
            params = call.call_args_list[1].kwargs['params']
            self.assertEqual(params['offset'], '100')
            self.assertEqual(params['value->publication->>published'], 'eq.true')
            self.assertNotIn('script', params['select'])

    def test_studio_pagination_preserves_owner_filter(self):
        store = VideoStore()
        first = Mock(); first.json.return_value = [{'value': {'id': str(i)}} for i in range(100)]
        second = Mock(); second.json.return_value = []
        with patch.object(store, 'call', side_effect=[first, second]) as call:
            self.assertEqual(len(store.list(owner='teacher')), 100)
            params = call.call_args_list[1].kwargs['params']
            self.assertEqual(params['offset'], '100')
            self.assertEqual(params['value->>owner_id'], 'eq.teacher')


if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        fixtures.NETWORK.stop()
        fixtures.ENV.stop()
        fixtures.TEMP.cleanup()
