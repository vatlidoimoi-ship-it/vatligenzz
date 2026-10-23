"""Teacher class reports display real class-scoped data and enforce ownership."""
import unittest
import test_role_flows as fixture

web = fixture.web


class TeacherClassReportsTests(unittest.TestCase):
    login = fixture.RoleFlowTests.login

    def setUp(self):
        fixture.RoleFlowTests.setUp(self)
        users = web.load_users()
        users.append({'id': 'student2', 'role': 'student', 'username': 'Trần Bình',
                      'email': 'student2@example.test', 'password': 'unused'})
        web.save_users(users)
        other = dict(self.course, id='course_other', teacher_id='teacher2', title='Lớp khác')
        web.db._save_json(web.db.courses_file, [self.course, other])
        web.db._save_json(web.db.progress_file, [
            {'user_id': 'student', 'course_id': 'course_a', 'completed_lessons': ['lesson_a']},
            {'user_id': 'student2', 'course_id': 'course_a', 'completed_lessons': []},
            {'user_id': 'student2', 'course_id': 'course_other', 'completed_lessons': []},
        ])
        web._save_subject_exam_data('li', {'exams': [
            {'id': 'exam10', 'grade': '10', 'topic': 'Chuyển động', 'title': 'Đề chuyển động',
             'questions': [{'id': 1, 'number': 1, 'question': 'Câu hỏi',
                            'options': {'A': 'Đúng', 'B': 'Sai'}, 'correct_answer': 'A'}]},
            {'id': 'exam11', 'grade': '11', 'topic': 'Dao động', 'title': 'Đề lớp 11', 'questions': []},
        ]})
        web.write_json(web.writable_data_file('exam_results.json'), [
            {'user_id': 'student', 'subject': 'li', 'exam_id': 'exam10',
             'exam_title': 'Đề chuyển động', 'submitted_at': '10/05/2026 09:00:00',
             'result': {'total_score': 5, 'multiple_choice': {'correct_count': 1, 'total_questions': 2},
                        'wrong_answers': [{'question_number': 2, 'question_text': 'Câu sai',
                                           'user_answer': 'B', 'correct_answer': 'A', 'explanation': 'Giải thích'}]}},
            {'user_id': 'student', 'subject': 'li', 'exam_id': 'exam10',
             'exam_title': 'Đề chuyển động', 'submitted_at': '11/05/2026 09:00:00',
             'result': {'total_score': 10, 'multiple_choice': {'correct_count': 2, 'total_questions': 2},
                        'wrong_answers': []}},
            {'user_id': 'student', 'subject': 'li', 'exam_id': 'exam11',
             'exam_title': 'Đề lớp 11', 'submitted_at': '12/05/2026 09:00:00',
             'result': {'total_score': 1, 'multiple_choice': {'correct_count': 1, 'total_questions': 10}}},
        ])
        web.write_json(web.writable_data_file('physics_grades.json'), [
            {'student_id': 'student', 'course_id': 'course_a', 'tx1': 8.5,
             'average': 8.5, 'midterm': None, 'final': None},
        ])

    def test_class_navigation_and_student_report(self):
        self.login('teacher')
        dashboard = self.client.get('/teacher/dashboard')
        self.assertIn(b'/teacher/classes/course_a', dashboard.data)
        overview = self.client.get('/teacher/classes/course_a')
        self.assertEqual(overview.status_code, 200)
        self.assertIn('Trần Bình'.encode(), overview.data)
        self.assertIn(b'/teacher/classes/course_a/students/student', overview.data)
        report = self.client.get('/teacher/classes/course_a/students/student')
        self.assertEqual(report.status_code, 200)
        for text in ('Tổng quan & sơ đồ', 'Bảng điểm', 'Phân tích lỗi & sửa bài',
                     'Chi tiết kiến thức', 'Nhận xét & hoạt động', 'Câu sai', 'Chưa ghi nhận'):
            self.assertIn(text.encode(), report.data)
        self.assertNotIn('Đề lớp 11'.encode(), report.data)
        self.assertIn(b'50%', report.data)  # First attempt for this exam: 1/2.
        self.assertIn(b'7.5', report.data)  # Average of the two grade-10 attempts.
        self.assertIn(b'8.5/10', report.data)
        self.assertIn('Thường xuyên 1'.encode(), report.data)

    def test_teacher_cannot_see_another_class_or_unenrolled_student(self):
        self.login('teacher')
        self.assertEqual(self.client.get('/teacher/classes/course_other').status_code, 404)
        self.assertEqual(self.client.get('/teacher/classes/course_other/students/student2').status_code, 404)
        web.db._save_json(web.db.progress_file, [])
        self.assertEqual(self.client.get('/teacher/classes/course_a/students/student').status_code, 404)
        self.login('student')
        self.assertEqual(self.client.get('/teacher/classes/course_a').status_code, 302)
        self.login('admin')
        self.assertEqual(self.client.get('/teacher/classes/course_other').status_code, 200)

    def test_exam_minimum_counts_distinct_exams_instead_of_retries(self):
        student = web.get_user_by_id('student')
        rows = [{'user_id': 'student', 'exam_id': 'same'} for _ in range(5)]
        report = web.teacher_student_report_data(
            self.course, {}, student, {row['exam_id']: {} for row in rows}, rows, [])
        self.assertEqual(report['attempt_count'], 5)
        self.assertEqual(report['distinct_exams'], 1)
        self.assertEqual(report['exams_remaining'], 3)
        self.assertFalse(report['exam_minimum_met'])
        rows.extend({'user_id': 'student', 'exam_id': str(i)} for i in range(3))
        report = web.teacher_student_report_data(
            self.course, {}, student, {row['exam_id']: {} for row in rows}, rows, [])
        self.assertTrue(report['exam_minimum_met'])
        self.assertEqual(report['exams_remaining'], 0)

    def test_dashboard_completion_counts_submissions_not_lesson_mastery(self):
        web.db._save_json(web.db.submissions_file, [
            {'user_id': 'student', 'course_id': 'course_a', 'exercise_id': 'lesson_a', 'score': 20},
            {'user_id': 'student', 'course_id': 'course_a', 'exercise_id': 'lesson_a', 'score': 90},
            {'user_id': 'student', 'course_id': 'deleted_course', 'exercise_id': 'lesson_a'},
        ])
        stats = web.admin_dashboard_stats()
        self.assertEqual(stats['submissions'], 2)
        self.assertEqual(stats['completed_lessons'], 2)
        self.assertEqual(web.db.get_course_progress('student', 'course_a')['completed_lessons'], ['lesson_a'])

    def test_radar_uses_recorded_topics_when_three_are_available(self):
        exam_by_id = {f'exam{i}': {'topic': topic} for i, topic in enumerate(
            ('Chuyển động', 'Lực', 'Năng lượng'), 1)}
        rows = [{'user_id': 'student', 'exam_id': f'exam{i}',
                 'submitted_at': f'1{i}/05/2026 09:00:00',
                 'result': {'total_score': 10, 'multiple_choice':
                            {'correct_count': 2, 'total_questions': 2}}}
                for i in range(1, 4)]
        report = web.teacher_student_report_data(
            self.course, {'completed_lessons': []}, web.get_user_by_id('student'),
            exam_by_id, rows, [])
        self.assertEqual(len(report['radar']['axes']), 3)
        self.assertEqual(len(report['radar']['grids']), 5)
        self.assertTrue(report['radar']['polygon'])


if __name__ == '__main__':
    unittest.main()
