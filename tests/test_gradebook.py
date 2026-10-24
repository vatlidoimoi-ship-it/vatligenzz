"""Class grade entry runs against isolated files with no external services."""
import copy
import unittest
from unittest.mock import patch
import test_role_flows as fixture
from utils import gradebook
from utils import storage

web = fixture.web


class GradebookTests(unittest.TestCase):
    login = fixture.RoleFlowTests.login
    url = '/teacher/classes/course_a/gradebook'

    def setUp(self):
        fixture.RoleFlowTests.setUp(self)
        self.path = web.writable_data_file('physics_grades.json')
        web.write_json(self.path, [])
        web.db._save_json(web.db.progress_file, [{'user_id': 'student', 'course_id': 'course_a', 'completed_lessons': []}])
        self.login('teacher')

    def load(self, term='hk1'):
        response = self.client.get(self.url + '?term=' + term)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as state:
            token = state['gradebook_csrf']
        return token

    def change(self, scores=None, term='hk1', student='student'):
        rows = web.read_json(self.path, [])
        return {'student_id': student, 'version': gradebook.version(gradebook.find_row(rows, 'course_a', student, term)),
                'scores': {**dict.fromkeys(gradebook.FIELDS_BY_TERM[term]), **(scores if scores is not None else dict(tx1='8,5', tx2=8, tx3=9, midterm=0, final=9))}}

    def save(self, changes, token=None, term='hk1'):
        token = token or self.load(term)
        return self.client.post(self.url + '?term=' + term, json={'changes': changes}, headers={'X-CSRF-Token': token})

    def test_bulk_save_zero_comma_average_history_and_report(self):
        result = self.save([self.change()])
        self.assertEqual(result.status_code, 200)
        row = web.read_json(self.path, [])[0]
        self.assertEqual(row['tx1'], 8.5)
        self.assertEqual(row['midterm'], 0)
        self.assertEqual(row['average'], 6.6)
        self.assertEqual(row['history'][0]['actor_id'], 'teacher')
        self.assertEqual(row['history'][0]['after']['midterm'], 0)
        self.assertNotIn('password', result.get_data(as_text=True))
        page = self.client.get('/teacher/classes/course_a/students/student?term=hk1')
        self.assertIn(b'6.6/10', page.data)

    def test_terms_are_separate_and_blank_clears_average(self):
        self.save([self.change()])
        self.save([self.change(dict(tx1=10, tx2=10, tx3=10, tx4=10, midterm=10, final=10), term='hk2')], term='hk2')
        self.save([self.change(dict(tx1=8.5, midterm=8, final=None))])
        rows = web.read_json(self.path, [])
        self.assertIsNone(gradebook.find_row(rows, 'course_a', 'student', 'hk1')['average'])
        self.assertEqual(gradebook.find_row(rows, 'course_a', 'student', 'hk2')['average'], 10)
        page = self.client.get('/teacher/classes/course_a/students/student?term=hk2')
        self.assertIn('Học kì II'.encode(), page.data)
        self.assertIn(b'10.0/10', page.data)

    def test_validation_rejects_entire_batch(self):
        for bad in [-1, 11, True, 'NaN', 'Infinity', {}, '8.55']:
            scores = dict(tx1=bad, midterm=9, final=9)
            self.assertEqual(self.save([self.change(scores)]).status_code, 400, str(bad))
            self.assertEqual(web.read_json(self.path, []), [])
        self.assertEqual(self.save([self.change(student='outsider')]).status_code, 400)
        duplicate = self.change()
        self.assertEqual(self.save([duplicate, duplicate]).status_code, 400)

    def test_permissions_csrf_and_invalid_term(self):
        token = self.load()
        changes = [self.change()]
        self.assertEqual(self.client.post(self.url, json={'changes': changes}).status_code, 403)
        self.login('teacher2')
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.save(changes, token=token).status_code, 404)
        self.login('student')
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.login('admin')
        self.assertEqual(self.save(changes).status_code, 200)
        self.assertEqual(self.client.get(self.url + '?term=other').status_code, 400)

    def test_stale_editor_cannot_overwrite_and_legacy_data_preserved(self):
        legacy = {'student_id': 'student', 'course_id': 'course_a', 'term': 'hk1',
                  'tx1': 8, 'tx4': 7, 'average': 8, 'source_file': 'original.xls'}
        unrelated = {'student_id': 'other', 'course_id': 'other', 'term': 'hk2', 'tx1': 6}
        web.write_json(self.path, [legacy, unrelated])
        change = self.change()
        self.assertEqual(self.save([change]).status_code, 200)
        snapshot = copy.deepcopy(web.read_json(self.path, []))
        self.assertEqual(self.save([change]).status_code, 409)
        self.assertEqual(web.read_json(self.path, []), snapshot)
        self.assertEqual(snapshot[0]['tx4'], 7)
        self.assertEqual(snapshot[0]['source_file'], 'original.xls')
        self.assertEqual(snapshot[1], unrelated)
        self.assertEqual(snapshot[0]['history'][0]['before']['tx1'], 8)

    def test_no_op_preserves_imported_average(self):
        legacy = {'student_id': 'student', 'course_id': 'course_a', 'term': 'hk1', 'tx1': 8, 'average': 8}
        web.write_json(self.path, [legacy])
        self.save([self.change(dict(tx1=8, midterm=None, final=None))])
        self.assertEqual(web.read_json(self.path, []), [legacy])

    def test_semester_columns_and_reject_extra_fields(self):
        page = self.client.get(self.url + '?term=hk1')
        for field in gradebook.FIELDS_BY_TERM['hk1']:
            self.assertIn(('data-field="' + field + '"').encode(), page.data)
        self.assertNotIn(b'data-field="tx4"', page.data)
        page = self.client.get(self.url + '?term=hk2')
        self.assertIn(b'data-field="tx4"', page.data)
        change = self.change()
        change['scores']['tx4'] = 10
        self.assertEqual(self.save([change]).status_code, 400)

    def test_rounding_and_pending_average(self):
        self.assertEqual(gradebook.average(dict(tx1=8, tx2=8, tx3=8, midterm=8, final=8.4)), 8.2)
        self.assertIsNone(gradebook.average(dict(tx1=0)))

    def test_formulas_zeroes_and_annual_weight(self):
        hk1 = dict(tx1=7, tx2=8, tx3=9, midterm=8, final=9)
        hk2 = dict(tx1=8, tx2=9, tx3=9, tx4=10, midterm=9, final=10)
        self.assertEqual(gradebook.average(hk1, 'hk1'), 8.4)
        self.assertEqual(gradebook.average(hk2, 'hk2'), 9.3)
        self.assertEqual(gradebook.annual_average(8.4, 9.3), 9.0)
        self.assertIsNone(gradebook.annual_average(None, 9.3))
        self.assertEqual(gradebook.average(dict.fromkeys(gradebook.FIELDS_BY_TERM['hk2'], 0), 'hk2'), 0)
        self.assertIsNone(gradebook.average(hk1, 'hk2'))

    def test_year_table_is_readonly_and_updates_after_semester_saves(self):
        first = dict(tx1=7, tx2=8, tx3=9, midterm=8, final=9)
        second = dict(tx1=8, tx2=9, tx3=9, tx4=10, midterm=9, final=10)
        self.assertEqual(self.save([self.change(first)]).status_code, 200)
        missing = self.client.get(self.url + '?term=year')
        self.assertIn('Chưa đủ điểm'.encode(), missing.data)
        self.assertEqual(self.save([self.change(second, term='hk2')], term='hk2').status_code, 200)
        page = self.client.get(self.url + '?term=year')
        self.assertIn(b'data-annual>9.0', page.data)
        self.assertNotIn(b'data-field=', page.data)
        before = web.read_json(self.path, [])
        token = self.load()
        result = self.client.post(self.url + '?term=year', json={'changes': []}, headers={'X-CSRF-Token': token})
        self.assertEqual(result.status_code, 400)
        self.assertEqual(web.read_json(self.path, []), before)
        report = self.client.get('/teacher/classes/course_a/students/student?term=year')
        self.assertIn(b'9.0/10', report.data)
        self.assertIn('Trung bình cả năm'.encode(), report.data)

    def test_math_import_is_not_used_as_physics_and_original_is_preserved(self):
        legacy = {'student_id': 'student', 'course_id': 'course_a', 'term': 'hk1',
                  'source_file': 'class_mon_toan_hoc.xls', 'tx1': 2.5, 'average': 2.5}
        web.write_json(self.path, [legacy])
        displayed = gradebook.view_rows([legacy], 'course_a', [{'id': 'student'}], 'hk1')[0]
        self.assertTrue(all(score is None for score in displayed['scores'].values()))
        self.assertIsNone(displayed['average'])
        report = self.client.get('/teacher/classes/course_a/students/student')
        self.assertNotIn(b'2.5/10', report.data)
        self.assertEqual(web.read_json(self.path, []), [legacy])
        self.assertEqual(self.save([self.change()]).status_code, 200)
        saved = web.read_json(self.path, [])[0]
        self.assertEqual(saved['original_import']['tx1'], 2.5)
        self.assertEqual(saved['entry_source'], 'teacher_manual')
        self.assertEqual(saved['average'], 6.6)

    def test_old_manual_entry_keeps_scores_but_does_not_confirm_other_imported_fields(self):
        old = {'source_file': 'mon_toan.xls', 'updated_by': 'teacher', 'tx1': 8,
               'tx2': 2, 'midterm': 9, 'final': 10,
               'history': [{'after': {'tx1': 8, 'midterm': 9, 'final': 10}}]}
        scores = gradebook.scores_for(old, 'hk1')
        self.assertEqual(scores['tx1'], 8)
        self.assertIsNone(scores['tx2'])
        self.assertIsNone(gradebook.average(scores))

    def test_two_student_batch_saves_together_or_not_at_all(self):
        users = web.load_users()
        users.append({'id': 'student2', 'role': 'student', 'username': 'Second', 'password': 'unused'})
        web.save_users(users)
        web.db._save_json(web.db.progress_file, [
            {'user_id': uid, 'course_id': 'course_a', 'completed_lessons': []}
            for uid in ('student', 'student2')])
        first, second = self.change(), self.change(student='student2')
        second['scores']['final'] = 12
        self.assertEqual(self.save([first, second]).status_code, 400)
        self.assertEqual(web.read_json(self.path, []), [])
        second['scores']['final'] = 10
        self.assertEqual(self.save([first, second]).status_code, 200)
        self.assertEqual(len(web.read_json(self.path, [])), 2)


class AtomicRemoteGradebookTests(unittest.TestCase):
    def test_remote_compare_and_swap_rejects_race(self):
        from unittest.mock import Mock
        client = Mock()
        client.get.return_value.json.return_value = [{'value': [], 'updated_at': 'revision'}]
        client.patch.return_value.json.return_value = []
        with patch.object(storage, 'SUPABASE_BACKEND', True), patch.object(storage, 'http_session', return_value=client):
            with self.assertRaises(storage.ConcurrentJSONUpdate):
                storage.update_json_atomically(web.readable_data_file('physics_grades.json'), lambda rows: rows, [])
        self.assertEqual(client.patch.call_args.kwargs['params']['updated_at'], 'eq.revision')


if __name__ == '__main__':
    unittest.main()
