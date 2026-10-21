"""Check every newly authored exam through the student pages and scoring route."""
import json
from collections import Counter
from unittest import TestCase
from unittest.mock import patch

import test_role_flows as flow


class CurriculumGapExamsTests(TestCase):
    login = flow.RoleFlowTests.login
    post = flow.RoleFlowTests.post

    def setUp(self):
        flow.RoleFlowTests.setUp(self)
        self.bank = json.loads((flow.ROOT / 'data' / 'li.json').read_text(encoding='utf-8'))
        flow.web._save_subject_exam_data('li', self.bank)
        self.exams = [exam for exam in self.bank['exams']
                      if exam.get('batch_id') == 'curriculum-gaps-2026-v1']

    def test_unique_complete_questions_and_curriculum_coverage(self):
        self.assertEqual(len(self.exams), 10)
        self.assertEqual(len({exam['id'] for exam in self.bank['exams']}), len(self.bank['exams']))
        self.assertEqual(Counter(exam['grade'] for exam in self.bank['exams']),
                         {'10': 9, '11': 22, '12': 24})
        for exam in self.exams:
            self.assertIn(exam['semester'], {'hk1', 'hk2'})
            self.assertEqual(len(exam['questions']), 10)
            self.assertEqual([q['number'] for q in exam['questions']], list(range(1, 11)))
            for q in exam['questions']:
                self.assertEqual(set(q['options']), set('ABCD'))
                self.assertEqual(len(set(q['options'].values())), 4)
                self.assertIn(q['correct_answer'], q['options'])
                self.assertTrue(q['explanation'])

    def test_every_new_exam_renders_and_perfect_answers_score_ten(self):
        listing = self.client.get('/tracnghiem')
        self.assertEqual(listing.status_code, 200)
        self.assertIn(b'id="examSemesterFilter"', listing.data)
        self.assertIn(b'data-semester="hk1"', listing.data)
        self.assertIn(b'data-semester="hk2"', listing.data)
        for exam in self.exams:
            self.assertIn(exam['id'].encode(), listing.data)
            page = self.client.get(f"/tracnghiem/lam-bai/li/{exam['id']}")
            self.assertEqual(page.status_code, 200, exam['id'])
            answers = {str(q['number']): q['correct_answer'] for q in exam['questions']}
            with patch('utils.gemini_api.analyze_exam_results', return_value=None):
                submitted = self.post('/tracnghiem/nop-bai', subject='li',
                                      exam_id=exam['id'], answers=answers)
            self.assertEqual(submitted.status_code, 200, exam['id'])
            self.assertEqual(submitted.json['result']['total_score'], 10, exam['id'])
            result = self.client.get(f"/tracnghiem/ket-qua/li/{exam['id']}")
            self.assertEqual(result.status_code, 200, exam['id'])


if __name__ == '__main__':
    import unittest
    unittest.main()
