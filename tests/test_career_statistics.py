"""Completion tracking uses only package identity, without answers or scores."""
import json
import unittest

import test_role_flows as flow

ROOT = flow.ROOT
web = flow.web


class CareerStatisticsTests(unittest.TestCase):
    login = flow.RoleFlowTests.login

    def setUp(self):
        flow.RoleFlowTests.setUp(self)
        catalog = json.loads((ROOT / 'data/career_assessments.json').read_text(encoding='utf-8'))
        web.write_json(web.writable_data_file('career_assessments.json'), catalog)
        web.write_json(web.CAREER_COMPLETIONS_FILE, [])

    def test_completion_is_counted_without_answers_or_scores(self):
        response = self.client.post('/api/career-guidance/completion', json={'package_id': 'holland'})
        self.assertEqual(response.status_code, 200)
        rows = web.read_json(web.CAREER_COMPLETIONS_FILE, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]), {'user_id', 'package_id', 'completed_at'})
        stats = web.admin_dashboard_stats()
        self.assertEqual(stats['career_completions'], 1)
        self.assertEqual(stats['career_students'], 1)
        self.assertEqual(next(row['count'] for row in stats['career_rows'] if row['title'] == 'Holland / RIASEC'), 1)
        self.login('admin')
        page = self.client.get('/admin/forum-reports')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Lượt làm Tâm lí - hướng nghiệp'.encode(), page.data)

    def test_rejects_unlisted_package_and_private_payload(self):
        for payload in ({'package_id': 'missing'},
                        {'package_id': 'holland', 'answers': [1, 2]},
                        {'package_id': 'holland', 'score': 75}):
            self.assertEqual(self.client.post('/api/career-guidance/completion', json=payload).status_code, 400)
        self.assertEqual(web.read_json(web.CAREER_COMPLETIONS_FILE, []), [])

    def test_rejects_unauthenticated_and_non_student(self):
        self.client.get('/logout')
        self.assertEqual(self.client.post('/api/career-guidance/completion', json={'package_id': 'holland'}).status_code, 302)
        self.login('teacher')
        self.assertEqual(self.client.post('/api/career-guidance/completion', json={'package_id': 'holland'}).status_code, 403)


if __name__ == '__main__':
    unittest.main()
