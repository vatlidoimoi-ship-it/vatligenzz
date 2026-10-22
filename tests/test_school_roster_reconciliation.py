"""Validate the supplied six rosters and a read-only migration plan."""
import unittest
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.reconcile_school_rosters import COURSES, EXPECTED, build_plan, excel_rosters
import test_role_flows as fixture


class SchoolRosterReconciliationTests(unittest.TestCase):
    def test_excel_rosters_have_expected_unique_students_and_sparse_scores(self):
        rosters = excel_rosters()
        self.assertEqual({name: len(rows) for name, rows in rosters.items()}, EXPECTED)
        all_rows = [row for rows in rosters.values() for row in rows]
        self.assertEqual(len({row['code'] for row in all_rows}), 247)
        self.assertEqual(sum(row['scores']['tx1'] is not None for row in all_rows), 245)
        self.assertEqual(sum(row['scores']['midterm'] is not None for row in all_rows), 0)
        self.assertEqual(sum(row['scores']['final'] is not None for row in all_rows), 0)

    def test_plan_archives_old_students_and_assigns_correct_teachers(self):
        old = [{'id': f'old{i}', 'role': 'student',
                'username': f'Old {i}', 'class_name': '10A1' if i < 240 else None}
               for i in range(258)]
        old += [{'id': 'admin1', 'role': 'admin', 'username': 'Previous Admin'},
                {'id': 'teacher1', 'role': 'teacher', 'username': 'Existing Teacher'}]
        before = {'data/users.json': old, 'data/courses.json': [
            {'id': 'oldcourse', 'teacher_id': 'teacher1', 'title': 'Old course'}],
            'data/progress.json': [{'user_id': 'old0', 'course_id': 'oldcourse'}],
            'data/exam_results.json': [{'user_id': 'old0', 'exam_id': 'e'}],
            'data/submissions.json': [{'user_id': 'old1', 'course_id': 'oldcourse'}]}
        output, removed = build_plan(before, excel_rosters())
        self.assertEqual(len(removed), 258)
        users = output['data/users.json']
        self.assertEqual(Counter(u['class_name'] for u in users if u['role'] == 'student'), EXPECTED)
        self.assertEqual(next(u['username'] for u in users if u['role'] == 'admin'), 'Trần Văn Nguyên')
        self.assertEqual(len(output['data/physics_grades.json']), 247)
        self.assertEqual(output['data/exam_results.json'], [])
        self.assertEqual(output['data/submissions.json'], [])
        self.assertEqual(len(output['data/progress.json']), 247)
        courses = {c['title'].split()[-1]: c for c in output['data/courses.json']}
        self.assertEqual(set(courses), set(EXPECTED))
        self.assertEqual(courses['10A2']['teacher_id'], COURSES['10A2'][1])
        self.assertEqual(courses['11A5']['teacher_id'], 'admin1')
        self.assertEqual(courses['12A7']['teacher_id'], 'admin1')


class ImportedRosterFlowTests(unittest.TestCase):
    login = fixture.RoleFlowTests.login

    def setUp(self):
        fixture.RoleFlowTests.setUp(self)
        old = [{'id': f'old{i}', 'role': 'student',
                'username': f'Old {i}', 'class_name': '10A1' if i < 240 else None}
               for i in range(258)]
        old += [{'id': 'admin1', 'role': 'admin', 'username': 'Previous Admin'}]
        before = {'data/users.json': old, 'data/courses.json': [], 'data/progress.json': []}
        output, _ = build_plan(before, excel_rosters())
        web = fixture.web
        web.write_json(web.writable_data_file('users.json'), output['data/users.json'])
        web.write_json(web.db.courses_file, output['data/courses.json'])
        web.write_json(web.db.progress_file, output['data/progress.json'])
        web.write_json(web.writable_data_file('physics_grades.json'), output['data/physics_grades.json'])

    def test_teacher_sees_correct_roster_and_excel_score(self):
        self.login('gv_excel_10a1')
        page = self.client.get('/teacher/classes/lop2026_10a1')
        self.assertEqual(page.status_code, 200)
        self.assertIn('44 em'.encode(), page.data)
        student = next(u for u in fixture.web.load_users()
                       if u.get('role') == 'student' and u.get('class_name') == '10A1')
        report = self.client.get('/teacher/classes/lop2026_10a1/students/' + student['id'])
        self.assertEqual(report.status_code, 200)
        self.assertIn(student['full_name'].encode(), report.data)
        self.assertIn(student['student_code'].encode(), report.data)
        self.login('gv_excel_10a2')
        self.assertEqual(self.client.get('/teacher/classes/lop2026_10a1').status_code, 404)
        self.login('admin1')
        self.assertEqual(self.client.get('/teacher/classes/lop2026_11a5').status_code, 200)


if __name__ == '__main__':
    unittest.main()
